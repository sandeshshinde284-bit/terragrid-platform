"""
Feature 1: Data Ingestion Service
Orchestrates fetching from multiple APIs and storing in database
"""
import os
import logging
from backend.config import settings
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .nasa_eonet import NASAEONETService
from .gdacs import GDACSService
from .usgs_earthquake import USGSEarthquakeService
from .noaa import NOAAService
from .openweather import OpenWeatherService
# Code below is kept for future use when IMD API approval is done
# from .imd_weather import IMDWeatherService
from .pubsub_service import PubSubService
from .impact_analysis import ImpactAnalysisService
from .lineage_tracker import LineageTracker
from backend.utils.data_logger import log_raw_data

logger = logging.getLogger(__name__)

class DataIngestionService:
    """Orchestrates real-time data ingestion from multiple sources"""
    
    def __init__(self, db_session: AsyncSession = None):
        self.db = db_session
        self.pubsub = PubSubService()
    
    async def ingest_all_sources(self, use_mock: bool = False, db_session = None) -> Dict[str, Any]:
        """
        Fetch data from all configured sources
        
        Args:
            use_mock: If True, use mock data for testing
            db_session: Database session for persistence
            
        Returns:
            Summary of ingestion results
        """
        logger.info("Starting data ingestion from all sources...")
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "sources": {},
            "total_events": 0,
            "total_published": 0,
            "events": [],
            "errors": []
        }
        
        # Override instance db if one is provided
        current_db = db_session if db_session else self.db
        
        try:
            # Check global mock configuration
            if settings.USE_MOCK_DATA:
                use_mock = True
                
            # 1. Fetch from all 5 sources concurrently in parallel using asyncio.gather
            logger.info("Fetching from all sources in parallel (NASA, GDACS, USGS, OpenWeather, NOAA)...")
            tasks = [
                NASAEONETService.fetch_events(use_mock=use_mock),
                GDACSService.fetch_events(use_mock=use_mock),
                USGSEarthquakeService.fetch_events(use_mock=use_mock),
                OpenWeatherService.fetch_events(),
                NOAAService.fetch_events(use_mock=use_mock),
            ]
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            source_names = ["nasa_eonet", "gdacs", "usgs_earthquakes", "openweather", "noaa_weather"]
            
            all_events = []
            for name, resp in zip(source_names, responses):
                if isinstance(resp, Exception):
                    logger.error(f"Error fetching from {name}: {resp}")
                    results["sources"][name] = {"count": 0, "status": f"error: {str(resp)}"}
                    results["errors"].append(f"{name}: {str(resp)}")
                elif isinstance(resp, list):
                    results["sources"][name] = {"count": len(resp), "status": "success"}
                    all_events.extend(resp)
                    # Raw cross-check log, folder-wise per source - see
                    # backend/utils/data_logger.py. Separate from the
                    # [FEATURE_HEALTH] summary line above/below, which stays
                    # a lightweight count+status only.
                    log_raw_data(name, resp)
                else:
                    results["sources"][name] = {"count": 0, "status": "empty"}
            
            results["total_events"] = len(all_events)
            
            # Code preserved for future use if IMD opens their API
            # 
            # if india_events:
            #     logger.info(f"[IMD] Found {len(india_events)} incidents in India, fetching additional IMD data...")
            #     imd_tasks = [
            #         IMDWeatherService.fetch_events(
            #             latitude=e.get("latitude", 0),
            #             longitude=e.get("longitude", 0),
            #             use_mock=use_mock
            #         )
            #         for e in india_events
            #     ]
            #     imd_responses = await asyncio.gather(*imd_tasks, return_exceptions=True)
            #     
            #     imd_total = 0
            #     for resp in imd_responses:
            #         if isinstance(resp, list):
            #             all_events.extend(resp)
            #             imd_total += len(resp)
            #     
            #     results["sources"]["imd_weather"] = {"count": imd_total, "status": "success"}
            #     logger.info(f"[IMD] Added {imd_total} additional weather events from IMD")
            # else:
            #     logger.info("[IMD] No India-based incidents detected, skipping IMD")
            #     results["sources"]["imd_weather"] = {"count": 0, "status": "no_india_incidents"}
            
            results["total_events"] = len(all_events)
            
            # 2. AI Batch Geocoding: Process all raw locations in 1 single Gemini request
            try:
                from .geocoding import geocoding_service
                batch_items = [
                    {
                        "raw_text": e.get("location_name", ""),
                        "lat": e.get("latitude", 0.0),
                        "lon": e.get("longitude", 0.0)
                    }
                    for e in all_events if e.get("location_name")
                ]
                clean_locations = geocoding_service.batch_format_locations(batch_items, db=current_db)
                for e in all_events:
                    raw_loc = e.get("location_name")
                    if raw_loc and raw_loc in clean_locations:
                        e["location_name"] = clean_locations[raw_loc]
            except Exception as batch_e:
                logger.warning(f"Batch geocoding step encountered error: {batch_e}")
            
            # 3. Process and store events
            logger.info(f"Processing {len(all_events)} events concurrently...")

            # Prefetch existing events to avoid duplicate inserts
            existing_event_map = None
            if current_db and all_events:
                try:
                    distinct_types = list({e.get("event_type") for e in all_events if e.get("event_type")})
                    
                    def _prefetch_map():
                        from ..models.event import Event
                        rows = current_db.query(Event).filter(Event.event_type.in_(distinct_types)).all()
                        return {
                            (round(row.latitude, 4), round(row.longitude, 4), row.event_type): row
                            for row in rows
                            if row.latitude is not None and row.longitude is not None
                        }
                    
                    existing_event_map = await asyncio.to_thread(_prefetch_map)
                    logger.debug(f"Pre-fetched {len(existing_event_map)} existing events into memory.")
                except Exception as pre_e:
                    logger.warning(f"Failed to pre-query existing events: {pre_e}")
                    existing_event_map = None

            for event in all_events:
                try:
                    await self._process_event(event, use_mock, current_db, existing_event_map)
                except Exception as e:
                    logger.error(f"Error processing event: {str(e)}")
                    results["errors"].append(str(e))

            if current_db:
                try:
                    current_db.commit()
                    logger.info("Batch database commit completed successfully.")
                except Exception as commit_e:
                    current_db.rollback()
                    logger.error(f"Batch database commit failed: {commit_e}")

            # Include processed events (with impact data) in the response
            results["events"] = [self._serialize_event(e) for e in all_events]
            
            logger.info(f"Data ingestion complete: {len(all_events)} events processed")
            return results
            
        except Exception as e:
            logger.error(f"Data ingestion failed: {str(e)}")
            results["errors"].append(str(e))
            return results
    
    @staticmethod
    def _serialize_event(event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert event dict (with datetime fields) into a JSON-serializable dict"""
        serialized = dict(event)
        timestamp = serialized.get("event_timestamp")
        if isinstance(timestamp, datetime):
            serialized["event_timestamp"] = timestamp.isoformat()
        ingested_at = serialized.get("ingested_at")
        if isinstance(ingested_at, datetime):
            serialized["ingested_at"] = ingested_at.isoformat()
        
        # Copy impact data to top level for frontend rendering
        impact = serialized.get('impact', {})
        # No invented defaults: a missing measurement stays None so the UI shows "unavailable".
        serialized['affectedArea'] = impact.get('affected_area_km2')
        serialized['affectedPopulation'] = impact.get('affected_population')
        serialized['threatScore'] = impact.get('risk_score')
        
        return serialized
    
    async def _process_event(self, event: Dict[str, Any], use_mock: bool = False, current_db = None, existing_event_map = None) -> None:
        """
        Process a single event through the 4-layer lineage pipeline:
        1. Record raw event data before enrichment (Layer 1)
        2. Validate required fields (Layer 2)
        3. Calculate impact analysis (Layer 3)
        4. Store in database and tie all layers together (Layer 4)
        Publish to Pub/Sub when complete.

        Args:
            event: Event data to process
            use_mock: Whether using mock data
            current_db: Database session for persisting alerts
            existing_event_map: In-memory cache of existing events for duplicate detection
        """
        pipeline_started_at = datetime.utcnow()
        raw_event_id = None
        validation_log_id = None
        enrichment_log_id = None

        try:
            # Source of Truth / Lineage - Layer 1: log this event exactly as it
            # arrived from its source adapter, before any enrichment touches it.
            # This isn't the raw HTTP body (fetch_events() already parsed that),
            # but it is the untouched per-event record before TerraGrid changes
            # anything about it - the honest boundary we can log without
            # rewriting all 5 source adapters to thread raw bodies through.
            pre_enrichment_snapshot = {k: v for k, v in event.items() if not isinstance(v, datetime)}
            if current_db:
                raw_event_id = await asyncio.to_thread(
                    LineageTracker.log_raw_event,
                    current_db,
                    event.get("source", "unknown"),
                    pre_enrichment_snapshot,
                    200,
                )

                # Layer 2: minimal structural validation - the same fields the
                # DB write below actually requires. Real failures here (missing
                # coordinates, no event_type) would otherwise fail silently
                # later when _store_event_sync tries to key off them.
                validation_errors = []
                if event.get("latitude") is None or event.get("longitude") is None:
                    validation_errors.append({"coordinates": "missing latitude/longitude"})
                if not event.get("event_type"):
                    validation_errors.append({"event_type": "missing event_type"})
                if not event.get("location_name"):
                    validation_errors.append({"location_name": "missing location_name"})
                validation_status = "FAIL" if validation_errors else "PASS"

                validation_log_id = await asyncio.to_thread(
                    LineageTracker.log_validation,
                    current_db,
                    raw_event_id,
                    validation_status,
                    validation_errors or None,
                )

            # Store in database FIRST, before impact analysis - so that a
            # brand-new event already has a real DB row (and id) by the time
            # calculate_impact() below may synchronously call
            # send_critical_alert(). That function looks up the matching
            # Event by (latitude, longitude, event_type) to attach its Alert
            # record; when storage happened AFTER impact calculation (the
            # original order), that lookup always found nothing for a
            # brand-new event, so the very first critical alert for any new
            # incident sent a real email but silently never got an Alert row
            # - invisible in the Alerts tab and unprotected by the DB-backed
            # dedup check (risking a duplicate email after a cold start).
            # Storing first fixes both: the lookup now finds the row, and the
            # impact/ingested_at fields are merged into it with a cheap
            # follow-up update right below.
            final_event_id = None
            if current_db:
                final_event_id = await asyncio.to_thread(self._store_event_sync, event, current_db, existing_event_map)
            elif self.db:
                await self._store_event(event)

            # Stamp the canonical DB id onto the event so the ingest response
            # uses the same identifier as GET /incidents (event_<pk>). Without
            # this the dashboard showed the source's own id (e.g. a GDACS
            # eventid) while the incidents list showed event_<pk>, so the same
            # flood had two different ids on two screens.
            if final_event_id is not None:
                event["id"] = f"event_{final_event_id}"

            # Calculate impact analysis (pass db_session for alert persistence).
            # Run via asyncio.to_thread: this call can synchronously perform
            # blocking Gmail SMTP I/O (with retry sleeps) inside
            # send_critical_alert() when risk_score >= 80 - without
            # offloading it, that would block this worker's entire event
            # loop (all other in-flight requests) for the duration.
            impact = await asyncio.to_thread(ImpactAnalysisService.calculate_impact, event, db_session=current_db)

            # Merge impact into event (in-memory, for Pub/Sub publish below)
            event["impact"] = impact
            event["ingested_at"] = datetime.utcnow().isoformat()

            # Persist the impact/ingested_at fields onto the row just stored
            # above, now that we know its id.
            if current_db and final_event_id is not None:
                await asyncio.to_thread(
                    self._merge_impact_into_event_sync, final_event_id, impact, event["ingested_at"], current_db
                )

            # Layer 3: log the enrichment ImpactAnalysisService just performed -
            # the event as received vs. the risk/impact fields it added.
            if current_db and validation_log_id is not None:
                enrichment_log_id = await asyncio.to_thread(
                    LineageTracker.log_enrichment,
                    current_db,
                    validation_log_id,
                    "impact_analysis",
                    "ImpactAnalysisService",
                    pre_enrichment_snapshot,
                    {k: v for k, v in impact.items() if not isinstance(v, datetime)} if isinstance(impact, dict) else impact,
                )

            # Layer 4: tie all 4 layers together now that we know the stored
            # event's real DB id. Only create the chain when every upstream
            # layer actually succeeded - a partial chain would be worse than
            # no chain, since get_incident_lineage() treats "found" as "complete".
            if current_db and final_event_id is not None and None not in (raw_event_id, validation_log_id, enrichment_log_id):
                elapsed_ms = int((datetime.utcnow() - pipeline_started_at).total_seconds() * 1000)
                await asyncio.to_thread(
                    LineageTracker.create_lineage_chain,
                    current_db,
                    raw_event_id,
                    validation_log_id,
                    enrichment_log_id,
                    final_event_id,
                    "COMPLETE" if validation_status == "PASS" else "PARTIAL",
                    elapsed_ms,
                )

            # Publish to Pub/Sub if not using mock
            if not use_mock:
                await self.pubsub.publish_event(event)

            logger.debug(f"Processed event: {event.get('location_name')}")

        except Exception as e:
            logger.error(f"Error in event processing: {str(e)}")
            raise

    def _store_event_sync(self, event_data: Dict[str, Any], db, existing_event_map: Dict = None) -> Optional[int]:
        """
        Synchronously store event in database (used by background polling)
        Optimized with Speed Win #5 (in-memory lookup) and Speed Win #8 (db.flush)

        Returns:
            The stored/updated event's DB id, or None if the write failed
            (needed by the lineage chain, which must point at a real Layer 4
            record, not whatever id the event dict happened to carry in).
        """
        try:
            from ..models.event import Event
            
            lat = event_data.get("latitude")
            lon = event_data.get("longitude")
            evt_type = event_data.get("event_type")
            
            # Issue A: Look up in pre-loaded memory dict; ONLY query DB if prefetch failed completely
            existing_event = None
            key = (round(lat, 4), round(lon, 4), evt_type) if lat is not None and lon is not None else None
            
            if existing_event_map is not None:
                # Map is a complete snapshot for this batch's event types: trust it directly!
                existing_event = existing_event_map.get(key) if key else None
            else:
                # Fallback only if prefetch failed
                existing_event = db.query(Event).filter(
                    Event.latitude == lat,
                    Event.longitude == lon,
                    Event.event_type == evt_type
                ).first()
            
            # Sanitize datetimes for JSONB storage
            import json
            def sanitize_dict(d):
                clean = {}
                for k, v in d.items():
                    if isinstance(v, datetime):
                        clean[k] = v.isoformat()
                    elif isinstance(v, dict):
                        clean[k] = sanitize_dict(v)
                    elif isinstance(v, list):
                        clean[k] = [sanitize_dict(i) if isinstance(i, dict) else i for i in v]
                    else:
                        clean[k] = v
                return clean
                
            safe_event_data = sanitize_dict(event_data)
            
            # Location name is already cleanly formatted by upstream Batch Geocoding
            location_name = event_data.get("location_name", "Unknown Location")
            
            # Issue B: Isolate this event in a SAVEPOINT so a single bad event never rolls back prior valid events!
            with db.begin_nested():
                if not existing_event:
                    # Create database record
                    db_event = Event(
                        event_type=evt_type,
                        severity=event_data.get("severity", "unknown"),
                        status=event_data.get("status", "active"),
                        latitude=lat,
                        longitude=lon,
                        location_name=location_name,
                        source=event_data.get("source", "unknown"),
                        event_timestamp=event_data.get("event_timestamp") if isinstance(event_data.get("event_timestamp"), datetime) else datetime.utcnow(),
                        confidence=event_data.get("confidence"),
                        is_verified=event_data.get("is_verified"),
                        data=safe_event_data  # Store sanitized JSON
                    )

                    db.add(db_event)
                    # Batch flush to group database operations
                    db.flush()
                    if existing_event_map is not None and key:
                        existing_event_map[key] = db_event
                    logger.debug(f"Flushed new event to session: {evt_type} at {lat},{lon}")
                    return db_event.id
                else:
                    # Update existing event
                    # Preserve internally generated data during polling updates
                    preserved_data = dict(existing_event.data or {})
                    preserved_data.update(safe_event_data)
                    existing_event.data = preserved_data

                    existing_event.severity = event_data.get("severity", existing_event.severity)
                    existing_event.location_name = location_name
                    existing_event.updated_at = datetime.utcnow()
                    db.flush()
                    logger.debug(f"Flushed updated event to session: {evt_type} at {lat},{lon}")
                    return existing_event.id

        except Exception as e:
            # Savepoint automatically rolls back on error; do not call rollback()
            # to avoid discarding previously processed events
            logger.error(f"Failed to store event in database (savepoint rolled back): {str(e)}")
            return None

    def _merge_impact_into_event_sync(self, event_id: int, impact: Dict[str, Any], ingested_at_iso: str, db) -> None:
        """
        Follow-up to _store_event_sync: merges the impact analysis (computed
        after that initial store, see _process_event) into the same row's
        `data` JSONB, now that we know its real id. Isolated in its own
        savepoint, same reasoning as _store_event_sync - a failure here must
        never roll back other events already flushed in this batch, and must
        never block the critical alert email, which has already been sent
        (or attempted) by the time this runs.
        """
        try:
            from ..models.event import Event
            with db.begin_nested():
                db_event = db.query(Event).filter(Event.id == event_id).first()
                if db_event:
                    data = dict(db_event.data or {})
                    data["impact"] = impact
                    data["ingested_at"] = ingested_at_iso
                    db_event.data = data
                    db_event.updated_at = datetime.utcnow()
                    db.flush()
        except Exception as e:
            logger.warning(f"Could not merge impact into stored event {event_id}: {str(e)}")

    async def _store_event(self, event: Dict[str, Any]) -> None:
        """Store event in database"""
        if not self.db:
            return
        
        try:
            from ..models.event import Event
            
            # Create database record
            db_event = Event(
                event_type=event.get("event_type"),
                severity=event.get("severity"),
                status=event.get("status"),
                latitude=event.get("latitude"),
                longitude=event.get("longitude"),
                location_name=event.get("location_name"),
                source=event.get("source"),
                event_timestamp=event.get("event_timestamp"),
                confidence=event.get("confidence"),
                is_verified=event.get("is_verified"),
                data=event  # Store entire event as JSON
            )
            
            self.db.add(db_event)
            await self.db.commit()
            
            logger.debug(f" Stored event in database: {event.get('location_name')}")
            
        except Exception as e:
            logger.error(f"Error storing event in database: {str(e)}")
            await self.db.rollback()
            raise
    
    async def get_recent_events(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get recent events from database
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of recent events
        """
        if not self.db:
            return []
        
        try:
            from ..models.event import Event
            from datetime import timedelta
            
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            
            stmt = select(Event).where(
                Event.event_timestamp >= cutoff
            ).order_by(Event.event_timestamp.desc())
            
            result = await self.db.execute(stmt)
            events = result.scalars().all()
            
            return [self._event_to_dict(e) for e in events]
            
        except Exception as e:
            logger.error(f"Error fetching recent events: {str(e)}")
            return []
    
    @staticmethod
    def _event_to_dict(event) -> Dict[str, Any]:
        """Convert Event model to dictionary"""
        return {
            "id": event.id,
            "event_type": event.event_type,
            "severity": event.severity,
            "status": event.status,
            "latitude": event.latitude,
            "longitude": event.longitude,
            "location_name": event.location_name,
            "source": event.source,
            "event_timestamp": event.event_timestamp.isoformat(),
            "confidence": event.confidence,
            "is_verified": event.is_verified,
            "created_at": event.created_at.isoformat() if event.created_at else None,
            "data": event.data
        }
