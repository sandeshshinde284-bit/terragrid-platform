"""
Feature 1: Data Ingestion Service
Orchestrates fetching from multiple APIs and storing in database
"""
import logging
import asyncio
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .nasa_eonet import NASAEONETService
from .gdacs import GDACSService
from .pubsub_service import PubSubService
from .impact_analysis import ImpactAnalysisService

logger = logging.getLogger(__name__)

class DataIngestionService:
    """Orchestrates real-time data ingestion from multiple sources"""
    
    def __init__(self, db_session: AsyncSession = None):
        self.db = db_session
        self.pubsub = PubSubService()
    
    async def ingest_all_sources(self, use_mock: bool = False) -> Dict[str, Any]:
        """
        Fetch data from all configured sources
        
        Args:
            use_mock: If True, use mock data for testing
            
        Returns:
            Summary of ingestion results
        """
        logger.info("🔄 Starting data ingestion from all sources...")
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "sources": {},
            "total_events": 0,
            "total_published": 0,
            "events": [],
            "errors": []
        }
        
        try:
            # Fetch from NASA EONET
            logger.info("📡 Fetching from NASA EONET...")
            nasa_events = await NASAEONETService.fetch_events(use_mock=use_mock)
            results["sources"]["nasa_eonet"] = {
                "count": len(nasa_events),
                "status": "success"
            }
            
            # Fetch from GDACS
            logger.info("📡 Fetching from GDACS...")
            gdacs_events = await GDACSService.fetch_events(use_mock=use_mock)
            results["sources"]["gdacs"] = {
                "count": len(gdacs_events),
                "status": "success"
            }
            
            # Combine events
            all_events = nasa_events + gdacs_events
            results["total_events"] = len(all_events)
            
            # Process and store events
            logger.info(f"💾 Processing {len(all_events)} events...")
            for event in all_events:
                try:
                    await self._process_event(event, use_mock)
                except Exception as e:
                    logger.error(f"Error processing event: {str(e)}")
                    results["errors"].append(str(e))
            
            # Include processed events (with impact data) in the response
            results["events"] = [self._serialize_event(e) for e in all_events]
            
            logger.info(f"✅ Data ingestion complete: {len(all_events)} events processed")
            return results
            
        except Exception as e:
            logger.error(f"❌ Data ingestion failed: {str(e)}")
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
        return serialized
    
    async def _process_event(self, event: Dict[str, Any], use_mock: bool = False) -> None:
        """
        Process a single event:
        1. Calculate impact
        2. Store in database
        3. Publish to Pub/Sub
        
        Args:
            event: Event data to process
            use_mock: Whether using mock data
        """
        try:
            # Calculate impact analysis
            impact = ImpactAnalysisService.calculate_impact(event)
            
            # Merge impact into event
            event["impact"] = impact
            event["ingested_at"] = datetime.utcnow().isoformat()
            
            # Store in database if session available
            if self.db:
                await self._store_event(event)
            
            # Publish to Pub/Sub if not using mock
            if not use_mock:
                await self.pubsub.publish_event(event)
            
            logger.debug(f"✅ Processed event: {event.get('location_name')}")
            
        except Exception as e:
            logger.error(f"Error in event processing: {str(e)}")
            raise
    
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
            
            logger.debug(f"✅ Stored event in database: {event.get('location_name')}")
            
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
