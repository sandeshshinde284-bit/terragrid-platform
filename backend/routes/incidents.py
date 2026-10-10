import logging
import json
import os
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models.event import Event
from backend.models.analysis import Analysis
from backend.models.alert import Alert

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])

# Load countries data once at startup
_COUNTRIES_DATA: Optional[Dict[str, Any]] = None

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "admin-secret-key")  # In production, use proper auth


def _load_countries_data() -> Dict[str, Any]:
    """Load countries.json for country name resolution"""
    global _COUNTRIES_DATA
    if _COUNTRIES_DATA is not None:
        return _COUNTRIES_DATA
    
    try:
        # Try frontend countries.json path first
        paths = [
            os.path.join(os.path.dirname(__file__), "../../frontend/src/data/countries.json"),
            os.path.join(os.path.dirname(__file__), "../data/countries.json"),
        ]
        
        for path in paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    _COUNTRIES_DATA = json.load(f)
                    logger.info(f"✓ Loaded countries.json from {path}")
                    return _COUNTRIES_DATA
        
        logger.warning("⚠ countries.json not found, using minimal fallback")
        return {"countries": {}, "aliases": {}}
    except Exception as e:
        logger.error(f"Failed to load countries.json: {e}, using fallback")
        return {"countries": {}, "aliases": {}}


def _get_country_name(country_code: str) -> str:
    """
    Convert country code to country name using countries.json.
    Falls back to the code itself if not found.
    """
    countries_data = _load_countries_data()
    countries_dict = countries_data.get("countries", {})
    
    # Try exact code match first
    if country_code in countries_dict:
        return countries_dict[country_code]
    
    # Log missing country for monitoring
    if country_code and country_code != "UN":
        logger.debug(f"Country code '{country_code}' not found in countries.json")
    
    return country_code or "Unknown"


def _resolve_country_code(location_name: str) -> str:
    """
    Extract country code from location_name string.
    
    **Strategy (in order):**
    1. If location ends with comma-separated part, extract last part (assume country code)
    2. Check aliases for fuzzy match (e.g., "United States" → "US")
    3. Return "UN" if unresolvable
    
    **Examples:**
    - "New Delhi, IN" → "IN"
    - "San Francisco, California, US" → "US"  (last part)
    - "United States" → "US"  (via alias)
    - "Unknown location" → "UN"
    """
    if not location_name:
        return "UN"
    
    countries_data = _load_countries_data()
    aliases = countries_data.get("aliases", {})
    
    # Strategy 1: Try extracting last comma-separated part
    parts = location_name.split(",")
    if len(parts) > 1:
        potential_code = parts[-1].strip()
        # Validate it looks like a country code (2-3 uppercase letters)
        if potential_code and 1 <= len(potential_code) <= 3 and potential_code.isupper():
            return potential_code
    
    # Strategy 2: Check aliases for exact match (case-insensitive)
    location_upper = location_name.upper().strip()
    if location_upper in aliases:
        return aliases[location_upper]
    
    # Strategy 3: Return UN for unknown
    logger.debug(f"Could not resolve country code from location: '{location_name}'")
    return "UN"


def find_incident_by_id(incident_id: str, db: Session) -> Optional[Event]:
    """
    **FIXED:** Safely resolves an incident by numeric ID, prefixed format (event_457, event-457, inc-457),
    or external JSONB ID without throwing PostgreSQL integer cast errors.
    
    **IMPORTANT:** Does NOT have a fallback to latest event. If ID is not found, returns None.
    This is intentional — the caller (route handler) should return 404.
    
    **Resolution strategy (in order):**
    1. If numeric or prefixed format (event_123), extract and query by db.id
    2. Query by external ID in data JSONB (nasa_id, gdacs_id, id field)
    3. Fallback scan recent 200 events for any ID match
    4. Return None if not found (caller handles 404)
    
    Args:
        incident_id: Can be "123", "event_123", "event-123", "inc-123", or external ID
        db: SQLAlchemy session
        
    Returns:
        Event object if found, None otherwise
    """
    clean_id = str(incident_id).strip()
    
    # 1. Extract database integer ID if numeric or prefixed
    db_id = None
    if clean_id.isdigit():
        db_id = int(clean_id)
    else:
        # Try common prefixes: event_123, event-123, inc-123, inc_123
        for prefix in ["event_", "event-", "inc_", "inc-"]:
            if clean_id.startswith(prefix):
                suffix = clean_id[len(prefix):].split("-")[0]  # Handle multiple dashes
                if suffix.isdigit():
                    db_id = int(suffix)
                    break
    
    # Query by primary key if we extracted a numeric ID
    if db_id is not None:
        event = db.query(Event).filter(Event.id == db_id).first()
        if event:
            logger.debug(f"[FIND_INCIDENT] Found by numeric ID: {incident_id} → {db_id}")
            return event
    
    # 2. Query by external ID in JSONB data
    try:
        event = db.query(Event).filter(
            (Event.data["id"].astext == clean_id) |
            (Event.data["nasa_id"].astext == clean_id) |
            (Event.data["gdacs_id"].astext == clean_id)
        ).first()
        if event:
            logger.debug(f"[FIND_INCIDENT] Found by external JSONB ID: {incident_id}")
            return event
    except Exception as e:
        logger.debug(f"[FIND_INCIDENT] JSONB query failed (expected for non-external IDs): {e}")
    
    # 3. Fallback scan recent events
    for evt in db.query(Event).order_by(desc(Event.id)).limit(200).all():
        if (str(evt.id) == clean_id or 
            f"event_{evt.id}" == clean_id or 
            f"event-{evt.id}" == clean_id or
            f"inc_{evt.id}" == clean_id or
            f"inc-{evt.id}" == clean_id):
            logger.debug(f"[FIND_INCIDENT] Found by scan: {incident_id} → {evt.id}")
            return evt
        
        data = evt.data or {}
        if (str(data.get("id")) == clean_id or 
            str(data.get("nasa_id")) == clean_id or 
            str(data.get("gdacs_id")) == clean_id):
            logger.debug(f"[FIND_INCIDENT] Found by data scan: {incident_id}")
            return evt
    
    # Not found — return None, let caller handle 404
    logger.debug(f"[FIND_INCIDENT] Not found: '{incident_id}'")
    return None


def _validate_mock_mode_access(use_mock: bool, admin_token: Optional[str] = None) -> bool:
    """
    Validate that mock mode is only enabled in development or by authorized users.
    
    In production, use_mock=true is only allowed with valid admin token.
    In development (use_mock via environment), always allowed.
    """
    if not use_mock:
        return True
    
    # If admin token is provided and valid, allow mock mode
    if admin_token and admin_token == ADMIN_TOKEN:
        logger.info("[MOCK-MODE] ✓ Authorized admin accessing mock mode")
        return True
    
    # In development, mock mode is allowed (relies on environment)
    dev_mode = os.getenv("ENVIRONMENT", "").lower() in ["dev", "development", "local"]
    if dev_mode:
        logger.debug("[MOCK-MODE] Development mode: mock access allowed")
        return True
    
    # Production + no token = deny
    logger.warning("[MOCK-MODE] ✗ Unauthorized mock mode access attempted in production")
    return False


@router.get("")
async def get_all_incidents(
    db: Session = Depends(get_db),
    limit: int = Query(100, description="Max incidents per page (1-1000)", ge=1, le=1000),
    offset: int = Query(0, description="Number of incidents to skip (pagination)", ge=0),
    status: str = Query(None, description="Filter by status (active, resolved, escalated)"),
    severity: str = Query(None, description="Filter by severity (critical, high, medium, low)"),
    event_type: str = Query(None, description="Filter by event type (earthquake, flood, etc.)")
):
    """
    Get historical incidents with pagination and filtering.
    
    **Used by:** Dashboard on startup to hydrate UI before WebSockets connect.
    
    **Pagination Example:**
    - GET /api/v1/incidents?limit=50&offset=0  (first 50)
    - GET /api/v1/incidents?limit=50&offset=50 (next 50)
    
    **Response strategy:** Database columns are authoritative and override JSONB data.
    """
    try:
        query = db.query(Event)
        
        # Apply filters
        if status:
            query = query.filter(Event.status == status)
        if severity:
            query = query.filter(Event.severity == severity)
        if event_type:
            query = query.filter(Event.event_type == event_type)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply ordering and pagination
        incidents = query.order_by(desc(Event.event_timestamp)).offset(offset).limit(limit).all()
        
        # Build response with database columns as source of truth
        result = []
        for incident in incidents:
            # Start with JSONB data, override with DB columns (authoritative)
            response_dict = incident.data.copy() if incident.data else {}
            
            # Preserve original ID if already prefixed, else add prefix
            original_id = response_dict.get('id') or response_dict.get('nasa_id') or response_dict.get('gdacs_id')
            if original_id and str(original_id).startswith(('event_', 'event-')):
                response_dict['id'] = original_id
            else:
                response_dict['id'] = f"event_{incident.id}"
            
            # Database columns are authoritative
            response_dict['location_name'] = incident.location_name or 'Unknown'
            response_dict['location'] = incident.location_name or 'Unknown'
            response_dict['latitude'] = incident.latitude
            response_dict['longitude'] = incident.longitude
            response_dict['severity'] = incident.severity or 'medium'
            response_dict['status'] = incident.status or 'active'
            response_dict['type'] = incident.event_type
            response_dict['event_type'] = incident.event_type
            response_dict['source'] = incident.source or 'unknown'
            response_dict['timestamp'] = incident.event_timestamp.isoformat() if incident.event_timestamp else None
            
            # Provide defaults for optional fields
            response_dict['affectedArea'] = response_dict.get('affectedArea', 0)
            response_dict['affectedPopulation'] = response_dict.get('affectedPopulation', 0)
            response_dict['threatScore'] = response_dict.get('threatScore', 50)
            
            result.append(response_dict)
        
        return {
            "data": result,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "returned": len(result),
                "has_more": offset + limit < total_count
            },
            "filters": {
                "status": status,
                "severity": severity,
                "event_type": event_type
            }
        }
        
    except Exception as e:
        logger.exception("Failed to query incidents from database")
        raise HTTPException(status_code=500, detail="Database query failed")


@router.get("/{incident_id}")
async def get_incident(incident_id: str, db: Session = Depends(get_db)):
    """Get specific incident details by ID (numeric, prefixed, or external ID)"""
    try:
        incident = find_incident_by_id(incident_id, db)
        if not incident:
            logger.warning(f"[GET_INCIDENT] 404: {incident_id}")
            raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")
        
        response = incident.data.copy() if incident.data else {}
        response['id'] = response.get('id') or f"event_{incident.id}"
        response['location_name'] = incident.location_name
        response['event_type'] = incident.event_type
        response['severity'] = incident.severity
        response['status'] = incident.status
        response['latitude'] = incident.latitude
        response['longitude'] = incident.longitude
        response['timestamp'] = incident.event_timestamp.isoformat() if incident.event_timestamp else None
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to fetch incident {incident_id}")
        raise HTTPException(status_code=500, detail="Failed to fetch incident")


@router.get("/{incident_id}/insights")
async def get_incident_insights(
    incident_id: str, 
    db: Session = Depends(get_db),
    use_mock: bool = Query(False, description="Bypass Gemini AI and return mock demonstration plan"),
    admin_token: str = Query(None, description="Admin token for mock mode access")
):
    """
    Generate AI Decision Support plan (Feature 6).
    Uses Gemini 1.5 Flash to synthesize tactical emergency actions for this incident.
    
    **Security:** use_mock=true requires admin token in production. Development mode allows unrestricted mock access.
    """
    try:
        # Validate mock mode access
        if use_mock and not _validate_mock_mode_access(use_mock, admin_token):
            logger.warning(f"[INSIGHTS] ✗ Unauthorized mock mode access for {incident_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Mock mode requires admin authorization in production"
            )
        
        incident = find_incident_by_id(incident_id, db)
        if not incident:
            logger.warning(f"[INSIGHTS] ✗ Incident not found: {incident_id}")
            raise HTTPException(status_code=404, detail=f"Incident not found: {incident_id}")
        
        incident_dict = incident.data.copy() if incident.data else {}
        incident_dict["location_name"] = incident.location_name
        incident_dict["event_type"] = incident.event_type
        incident_dict["severity"] = incident.severity
        incident_dict["latitude"] = incident.latitude
        incident_dict["longitude"] = incident.longitude
        
        # Calculate evacuation zones if available
        zone_data = None
        try:
            from backend.services.evacuation_zones import EvacuationZoneService
            zone_data = EvacuationZoneService.calculate_zones(incident_dict)
            logger.debug(f"[INSIGHTS] Zone data calculated for {incident_id}")
        except Exception as e:
            logger.debug(f"[INSIGHTS] Zone data unavailable: {e}")
            zone_data = None
        
        # Generate AI plan
        from backend.services.decision_support import get_decision_support_service
        plan = get_decision_support_service().generate_response_plan(incident_dict, zone_data, use_mock=use_mock)
        
        if not plan:
            logger.warning(f"[INSIGHTS] Empty plan returned for {incident_id}")
            raise HTTPException(status_code=500, detail="AI Decision Support failed to generate a plan")
        
        if plan.get("is_fallback"):
            logger.info(f"[INSIGHTS] Serving fallback plan (Gemini API unavailable)")
        elif use_mock:
            logger.info(f"[INSIGHTS] Demo mode: mock plan for {incident_id}")
        else:
            logger.info(f"[INSIGHTS] AI plan generated for {incident_id}")
        
        return {
            "status": "success",
            "incident_id": incident_id,
            "location": incident.location_name,
            "plan": plan,
            "is_mock": use_mock
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[INSIGHTS] Error for {incident_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")


@router.post("/{incident_id}/deep-analysis")
async def generate_deep_incident_analysis(
    incident_id: str, 
    db: Session = Depends(get_db),
    use_mock: bool = Query(False, description="Bypass Gemini and return mock dossier"),
    admin_token: str = Query(None, description="Admin token for mock mode access")
):
    """
    Tier 2 Deep Tactical AI Dossier: Exhaustive crisis intelligence (6h/12h/24h predictions,
    critical infrastructure, evacuation corridors, resource mobilization).
    Caches result in PostgreSQL Event.data['deep_dossier'].
    
    **Security:** use_mock=true requires admin token in production.
    """
    try:
        # Validate mock mode access
        if use_mock and not _validate_mock_mode_access(use_mock, admin_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Mock mode requires admin authorization in production"
            )
        
        incident = find_incident_by_id(incident_id, db)
        if not incident:
            logger.warning(f"[DEEP-DOSSIER] ✗ Not found: {incident_id}")
            raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
        
        raw_data = incident.data or {}
        incident_dict = {
            "id": incident.id,
            "event_type": incident.event_type,
            "location_name": incident.location_name,
            "latitude": incident.latitude,
            "longitude": incident.longitude,
            "source": incident.source,
            "severity": incident.severity,
            "impact": raw_data.get("impact") or {},
            "data": raw_data
        }
        
        from backend.services.decision_support import get_decision_support_service
        dossier = get_decision_support_service().generate_deep_tactical_dossier(
            incident_dict, 
            use_mock=use_mock, 
            db_session=db
        )
        
        # Cache dossier in PostgreSQL
        try:
            curr_data = dict(incident.data or {})
            curr_data["deep_dossier"] = dossier
            incident.data = curr_data
            db.commit()
            logger.info(f"[DEEP-DOSSIER] ✓ Cached for {incident_id}")
        except Exception as cache_err:
            logger.warning(f"[DEEP-DOSSIER] Cache failed: {cache_err}")
            db.rollback()
        
        return {
            "status": "success",
            "incident_id": incident_id,
            "location": incident.location_name,
            "dossier": dossier,
            "is_mock": use_mock
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[DEEP-DOSSIER] Error for {incident_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Deep analysis failed: {str(e)}")


@router.get("/{incident_id}/deep-dossier")
async def get_deep_incident_dossier(incident_id: str, db: Session = Depends(get_db)):
    """Retrieve cached Tier 2 Deep Tactical AI Dossier"""
    try:
        incident = find_incident_by_id(incident_id, db)
        if not incident:
            raise HTTPException(status_code=404, detail=f"Incident not found")
        
        dossier = (incident.data or {}).get("deep_dossier")
        if not dossier:
            return {
                "status": "pending",
                "incident_id": incident_id,
                "dossier": None,
                "message": "Deep analysis has not been generated for this incident"
            }
        
        return {
            "status": "success",
            "incident_id": incident_id,
            "dossier": dossier
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to retrieve dossier for {incident_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{incident_id}/analyses")
async def get_analyses(incident_id: str, db: Session = Depends(get_db)):
    """Get AI analysis history for an incident"""
    try:
        incident = find_incident_by_id(incident_id, db)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        analyses = db.query(Analysis).filter(Analysis.event_id == incident.id).order_by(desc(Analysis.created_at)).all()
        return analyses
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to fetch analyses for {incident_id}")
        raise HTTPException(status_code=500, detail="Failed to fetch analyses")


@router.get("/{incident_id}/alerts")
async def get_alerts(incident_id: str, db: Session = Depends(get_db)):
    """Get alerts sent for an incident"""
    try:
        incident = find_incident_by_id(incident_id, db)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        alerts = db.query(Alert).filter(Alert.event_id == incident.id).order_by(desc(Alert.created_at)).all()
        return alerts
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to fetch alerts for {incident_id}")
        raise HTTPException(status_code=500, detail="Failed to fetch alerts")


@router.get("/stats/overview")
async def get_incidents_stats(db: Session = Depends(get_db)):
    """
    Get incident statistics for dashboard overview.
    
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
            severity = (incident.severity or "unknown").lower()
            if severity in stats["by_severity"]:
                stats["by_severity"][severity] += 1
            else:
                stats["by_severity"]["unknown"] += 1
            
            # Count by type
            event_type = incident.event_type or "unknown"
            stats["by_type"][event_type] = stats["by_type"].get(event_type, 0) + 1
            
            # Count by country (use improved resolver)
            country_code = _resolve_country_code(incident.location_name)
            country_name = _get_country_name(country_code)
            
            stats["by_country"][country_code] = stats["by_country"].get(country_code, 0) + 1
            
            # Count by source
            source = incident.source or "unknown"
            stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
        
        # Get sorted list of affected countries
        stats["countries_affected"] = sorted(
            [
                {"code": code, "name": _get_country_name(code), "count": count}
                for code, count in stats["by_country"].items()
            ],
            key=lambda x: x["count"],
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
    event_type: str = Query(None, description="Filter by event type (earthquake, flood, etc.)"),
    limit: int = Query(100, description="Max incidents per country", ge=1, le=1000)
):
    """
    Get incidents grouped by country with optional filters.
    
    **Examples:**
    - GET /api/v1/incidents/grouped/by-country
    - GET /api/v1/incidents/grouped/by-country?country_code=IN
    - GET /api/v1/incidents/grouped/by-country?event_type=earthquake
    
    **Countries are resolved from location_name using intelligent extraction.**
    """
    try:
        query = db.query(Event).order_by(desc(Event.severity), desc(Event.event_timestamp))
        
        # Filter by event type if provided
        if event_type:
            query = query.filter(Event.event_type == event_type)
        
        # Limit total results
        incidents = query.limit(limit).all()
        
        # Group by country
        countries_dict = {}
        
        for incident in incidents:
            # Resolve country code intelligently
            resolved_code = _resolve_country_code(incident.location_name)
            
            # Skip if filtering by country and this doesn't match
            if country_code and resolved_code != country_code:
                continue
            
            if resolved_code not in countries_dict:
                countries_dict[resolved_code] = {
                    "country_code": resolved_code,
                    "country_name": _get_country_name(resolved_code),
                    "incidents": [],
                    "count": 0,
                    "critical_count": 0,
                    "high_count": 0,
                    "medium_count": 0,
                    "low_count": 0
                }
            
            # Prepare incident response
            incident_data = incident.data or {}
            incident_data['id'] = incident_data.get('id') or f"event_{incident.id}"
            incident_data['location'] = incident.location_name
            incident_data['type'] = incident.event_type
            incident_data['severity'] = incident.severity or 'medium'
            incident_data['status'] = incident.status or 'active'
            incident_data['latitude'] = incident.latitude
            incident_data['longitude'] = incident.longitude
            incident_data['threatScore'] = incident_data.get('threatScore', 50)
            incident_data['affectedArea'] = incident_data.get('affectedArea', 0)
            incident_data['affectedPopulation'] = incident_data.get('affectedPopulation', 0)
            incident_data['timestamp'] = incident.event_timestamp.isoformat() if incident.event_timestamp else None
            
            countries_dict[resolved_code]["incidents"].append(incident_data)
            countries_dict[resolved_code]["count"] += 1
            
            # Count by severity
            severity = (incident.severity or "medium").lower()
            if severity == "critical":
                countries_dict[resolved_code]["critical_count"] += 1
            elif severity == "high":
                countries_dict[resolved_code]["high_count"] += 1
            elif severity == "medium":
                countries_dict[resolved_code]["medium_count"] += 1
            else:
                countries_dict[resolved_code]["low_count"] += 1
        
        # Sort by critical incidents first, then by total count
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
