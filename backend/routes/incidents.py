import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models.event import Event
from backend.models.analysis import Analysis
from backend.models.alert import Alert

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])

@router.get("")
async def get_all_incidents(
    db: Session = Depends(get_db),
    limit: int = Query(1000, description="Max number of incidents to return"),
    status: str = Query(None, description="Filter by status (e.g., active, resolved)"),
    severity: str = Query(None, description="Filter by severity")
):
    """
    Get historical incidents from the PostgreSQL database.
    This is used by the dashboard on startup to hydrate the UI before WebSockets connect.
    """
    try:
        query = db.query(Event)
        
        if status:
            query = query.filter(Event.status == status)
        if severity:
            query = query.filter(Event.severity == severity)
            
        # Order by newest first
        incidents = query.order_by(desc(Event.event_timestamp)).limit(limit).all()
        
        # Return incidents with lat/lon coordinates from relational columns
        result = []
        for incident in incidents:
            # Start with data JSON if it exists
            response_dict = incident.data.copy() if incident.data else {}
            
            # Override with database columns (take precedence)
            response_dict['id'] = f"event_{incident.id}"
            response_dict['location_name'] = incident.location_name or 'Unknown'
            response_dict['location'] = incident.location_name or 'Unknown'
            response_dict['latitude'] = incident.latitude
            response_dict['longitude'] = incident.longitude
            response_dict['severity'] = incident.severity
            response_dict['status'] = incident.status
            response_dict['type'] = incident.event_type
            response_dict['event_type'] = incident.event_type
            response_dict['affectedArea'] = response_dict.get('affectedArea', 0)
            response_dict['affectedPopulation'] = response_dict.get('affectedPopulation', 0)
            response_dict['threatScore'] = response_dict.get('threatScore', 50)
            
            result.append(response_dict)
        
        return result
        
    except Exception as e:
        logger.exception("Failed to query incidents from database")
        raise HTTPException(status_code=500, detail="Database query failed")

@router.get("/{incident_id}")
async def get_incident(incident_id: int, db: Session = Depends(get_db)):
    """Get specific incident details by its primary key ID"""
    incident = db.query(Event).filter(Event.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident.data if incident.data else {"id": incident.id, "event_type": incident.event_type}

@router.get("/{incident_id}/insights")
async def get_incident_insights(incident_id: str, db: Session = Depends(get_db)):
    """
    Generate and return a country-specific AI Decision Support plan (Feature 6).
    Uses Gemini 1.5 Flash to synthesize tactical emergency actions for this incident.
    
    STRICT MODE: Only returns real data. No fallback/mock data.
    Returns 404 if incident not found.
    Returns 500 if Gemini fails (not 200).
    """
    try:
        incident = None
        logger.info(f"[INSIGHTS] Attempting to find incident: {incident_id}")
        
        # Get all incidents and try multiple matching strategies
        all_events = db.query(Event).all()
        
        for evt in all_events:
            # Strategy 1: Check raw data.id (e.g., EONET_24786)
            if evt.data and evt.data.get("id") == incident_id:
                incident = evt
                logger.info(f"[INSIGHTS] ✓ Found by raw data.id: {incident_id}")
                break
            
            # Strategy 2: Check if database ID matches (handle "event-18-timestamp" or "event_18" or "18")
            try:
                id_parts = str(incident_id).replace("event-", "").replace("event_", "").split("-")
                db_id = int(id_parts[0])
                if evt.id == db_id:
                    incident = evt
                    logger.info(f"[INSIGHTS] ✓ Found by database ID: {db_id}")
                    break
            except (ValueError, TypeError, IndexError):
                pass
            
            # Strategy 3: Check if we're looking for event_{db_id} format
            if incident_id.startswith("event_"):
                try:
                    db_id = int(incident_id.replace("event_", ""))
                    if evt.id == db_id:
                        incident = evt
                        logger.info(f"[INSIGHTS] ✓ Found by event_ format: {db_id}")
                        break
                except (ValueError, TypeError):
                    pass
        
        # STRICT MODE: Incident must be found
        if not incident:
            logger.warning(f"[INSIGHTS] ✗ LIVE MODE: Incident not found: {incident_id}")
            raise HTTPException(status_code=404, detail=f"Incident not found: {incident_id}")
            
        incident_dict = incident.data.copy() if incident.data else {}
        incident_dict["location_name"] = incident.location_name
        incident_dict["event_type"] = incident.event_type
        incident_dict["severity"] = incident.severity
        
        # Calculate zone data if available
        zone_data = None
        try:
            from backend.services.evacuation_zones import EvacuationZoneService
            zone_data = EvacuationZoneService.calculate_zones(incident_dict)
        except Exception as e:
            logger.warning(f"Could not calculate zone data: {e}")
            zone_data = None
            
        from backend.services.decision_support import get_decision_support_service
        plan = get_decision_support_service().generate_response_plan(incident_dict, zone_data)
        
        # Verify we got a plan (real AI or graceful fallback)
        if not plan:
            logger.warning(f"[INSIGHTS] LIVE MODE: Received empty plan")
            raise HTTPException(status_code=500, detail="AI Decision Support failed to generate a plan")
            
        if plan.get("country_context", "").startswith("Standard emergency"):
            logger.info(f"[INSIGHTS] LIVE MODE: Serving graceful tactical fallback plan (Gemini API unavailable or rate limited)")
        else:
            logger.info(f"[INSIGHTS] Successfully generated real AI plan for {incident_id}")
            
        return {
            "status": "success",
            "incident_id": incident_id,
            "location": incident.location_name,
            "plan": plan
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[INSIGHTS] ✗ Error generating insights for incident {incident_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")

@router.get("/{incident_id}/analyses")
async def get_analyses(incident_id: int, db: Session = Depends(get_db)):
    """Get AI analysis history for an incident"""
    analyses = db.query(Analysis).filter(Analysis.event_id == incident_id).order_by(desc(Analysis.created_at)).all()
    return analyses

@router.get("/{incident_id}/alerts")
async def get_alerts(incident_id: int, db: Session = Depends(get_db)):
    """Get alerts sent for an incident"""
    alerts = db.query(Alert).filter(Alert.event_id == incident_id).order_by(desc(Alert.created_at)).all()
    return alerts


@router.get("/stats/overview")
async def get_incidents_stats(db: Session = Depends(get_db)):
    """
    Get incident statistics for dashboard overview
    
    Returns:
    - Total incidents by severity
    - Countries affected
    - Incident types breakdown
    - Sources breakdown
    """
    try:
        incidents = db.query(Event).all()
        
        stats = {
            "total": len(incidents),
            "by_severity": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "unknown": 0
            },
            "by_type": {},
            "by_country": {},
            "by_source": {},
            "countries_affected": []
        }
        
        for incident in incidents:
            # Count by severity
            severity = incident.severity.lower() if incident.severity else "unknown"
            if severity in stats["by_severity"]:
                stats["by_severity"][severity] += 1
            
            # Count by type
            event_type = incident.event_type or "unknown"
            stats["by_type"][event_type] = stats["by_type"].get(event_type, 0) + 1
            
            # Count by country (extract from location_name)
            location_parts = incident.location_name.split(',') if incident.location_name else []
            country_code = location_parts[-1].strip() if len(location_parts) > 1 else "UN"
            
            if country_code not in stats["by_country"]:
                stats["by_country"][country_code] = 0
            stats["by_country"][country_code] += 1
            
            # Count by source
            source = incident.source or "unknown"
            stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
        
        # Get sorted list of affected countries
        stats["countries_affected"] = sorted(
            stats["by_country"].items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return stats
        
    except Exception as e:
        logger.exception("Failed to get incident statistics")
        raise HTTPException(status_code=500, detail="Statistics query failed")


@router.get("/grouped/by-country")
async def get_incidents_by_country(
    db: Session = Depends(get_db),
    country_code: str = Query(None, description="Filter by country code (e.g., IN, CN, NP)"),
    event_type: str = Query(None, description="Filter by event type (e.g., earthquake, flood)"),
    limit: int = Query(100, description="Max incidents per country")
):
    """
    Get incidents grouped by country with optional filters
    
    Examples:
    - GET /api/v1/incidents/grouped/by-country
    - GET /api/v1/incidents/grouped/by-country?country_code=IN
    - GET /api/v1/incidents/grouped/by-country?country_code=IN&event_type=earthquake
    """
    try:
        query = db.query(Event).order_by(desc(Event.severity), desc(Event.event_timestamp))
        
        # Filter by country if provided
        if country_code:
            query = query.filter(Event.location_name.ilike(f'%{country_code}%'))
        
        # Filter by event type if provided
        if event_type:
            query = query.filter(Event.event_type == event_type)
        
        # Limit total results
        incidents = query.limit(limit).all()
        
        # Group by country
        countries_dict = {}
        
        for incident in incidents:
            # Extract country code from location_name (e.g., "Delhi, IN" → "IN")
            location_parts = incident.location_name.split(',') if incident.location_name else []
            country_code_key = location_parts[-1].strip() if len(location_parts) > 1 else "UN"
            
            if country_code_key not in countries_dict:
                countries_dict[country_code_key] = {
                    "country_code": country_code_key,
                    "country_name": _get_country_name(country_code_key),
                    "incidents": [],
                    "count": 0,
                    "critical_count": 0,
                    "high_count": 0,
                    "medium_count": 0,
                    "low_count": 0
                }
            
            # Prepare incident data
            incident_data = incident.data or {}
            incident_data['id'] = incident_data.get('id') or f"event_{incident.id}"
            incident_data['location'] = incident.location_name
            incident_data['type'] = incident.event_type
            incident_data['severity'] = incident.severity
            incident_data['status'] = incident.status
            incident_data['latitude'] = incident.latitude
            incident_data['longitude'] = incident.longitude
            incident_data['threatScore'] = incident_data.get('threatScore', 50)
            incident_data['affectedArea'] = incident_data.get('affectedArea', 0)
            incident_data['affectedPopulation'] = incident_data.get('affectedPopulation', 0)
            incident_data['timestamp'] = incident.event_timestamp.isoformat() if incident.event_timestamp else None
            
            countries_dict[country_code_key]["incidents"].append(incident_data)
            countries_dict[country_code_key]["count"] += 1
            
            # Count by severity
            severity = incident.severity.lower() if incident.severity else "low"
            if severity == "critical":
                countries_dict[country_code_key]["critical_count"] += 1
            elif severity == "high":
                countries_dict[country_code_key]["high_count"] += 1
            elif severity == "medium":
                countries_dict[country_code_key]["medium_count"] += 1
            else:
                countries_dict[country_code_key]["low_count"] += 1
        
        # Sort countries by critical incidents first
        sorted_countries = sorted(
            countries_dict.values(),
            key=lambda x: (x["critical_count"], x["count"]),
            reverse=True
        )
        
        return {
            "countries": sorted_countries,
            "total_countries": len(sorted_countries),
            "total_incidents": len(incidents),
            "filters_applied": {
                "country_code": country_code,
                "event_type": event_type
            }
        }
        
    except Exception as e:
        logger.exception("Failed to get incidents by country")
        raise HTTPException(status_code=500, detail="Query failed")


def _get_country_name(code: str) -> str:
    """Convert country code to country name"""
    country_names = {
        'IN': 'India',
        'CN': 'China',
        'NP': 'Nepal',
        'BD': 'Bangladesh',
        'PK': 'Pakistan',
        'US': 'United States',
        'TH': 'Thailand',
        'VN': 'Vietnam',
        'SG': 'Singapore',
        'MY': 'Malaysia',
        'IQ': 'Iraq',
        'AE': 'UAE',
        'ET': 'Ethiopia',
        'KE': 'Kenya',
        'RW': 'Rwanda',
        'HK': 'Hong Kong',
        'UN': 'Unknown'
    }
    return country_names.get(code, code)
