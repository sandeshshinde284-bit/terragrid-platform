"""
Feature 3A: Evacuation Zones API Routes
Endpoints for zone calculation, safe routes, and resource planning
"""
import logging
from fastapi import APIRouter, HTTPException, Query, Path
from typing import List, Dict, Any

from backend.services.evacuation_zones import EvacuationZoneService
from backend.services.polling import get_polling_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/zones", tags=["zones"])


@router.get("/calculate/{incident_id}")
async def calculate_zones_for_incident(incident_id: str) -> Dict[str, Any]:
    """
    Calculate evacuation zones for a specific incident
    
    Args:
        incident_id: Incident identifier
    
    Returns:
        zones_data: {
            incident_center, zones: [...], evacuation_times, population_affected
        }
    """
    try:
        # Get incident from polling service cache
        polling_service = get_polling_service()
        all_incidents = polling_service.get_incidents()
        
        incident = None
        for inc in all_incidents:
            if (inc.get("data", {}).get("nasa_id") == incident_id or
                inc.get("data", {}).get("usgs_id") == incident_id or
                inc.get("location_name", "").lower() == incident_id.lower()):
                incident = inc
                break
        
        if not incident:
            raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
        
        zones_data = EvacuationZoneService.calculate_zones(incident)
        
        return {
            "status": "success",
            "data": zones_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating zones: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate")
async def calculate_zones_for_coords(
    latitude: float = Query(..., description="Incident latitude"),
    longitude: float = Query(..., description="Incident longitude"),
    severity: str = Query("medium", description="Severity: low/medium/high/critical"),
    event_type: str = Query("other", description="Event type: earthquake/fire/flood/hurricane/tornado/storm/volcano/other"),
    location_name: str = Query("Incident Location", description="Location name"),
    threat_score: int = Query(50, ge=0, le=100, description="Threat score 0-100"),
) -> Dict[str, Any]:
    """
    Calculate evacuation zones from coordinates
    
    Args:
        latitude: Incident latitude
        longitude: Incident longitude
        severity: low/medium/high/critical
        event_type: Type of disaster
        location_name: Location name
        threat_score: Threat score 0-100
    
    Returns:
        zones_data with 4 concentric evacuation zones
    """
    try:
        incident = {
            "latitude": latitude,
            "longitude": longitude,
            "severity": severity,
            "event_type": event_type,
            "location_name": location_name,
            "threat_score": threat_score,
        }
        
        zones_data = EvacuationZoneService.calculate_zones(incident)
        
        return {
            "status": "success",
            "data": zones_data
        }
        
    except Exception as e:
        logger.error(f"Error calculating zones: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all")
async def get_zones_for_all_incidents() -> Dict[str, Any]:
    """
    Calculate evacuation zones for all active incidents
    
    Returns:
        incidents_with_zones: [
            {incident_data, zones: [...], population_affected}
        ]
    """
    try:
        polling_service = get_polling_service()
        all_incidents = polling_service.get_incidents()
        
        incidents_with_zones = []
        for incident in all_incidents[:20]:  # Limit to top 20 for performance
            try:
                zones_data = EvacuationZoneService.calculate_zones(incident)
                incident_result = {
                    "incident": {
                        "location": incident.get("location_name"),
                        "latitude": incident.get("latitude"),
                        "longitude": incident.get("longitude"),
                        "severity": incident.get("severity"),
                        "event_type": incident.get("event_type"),
                        "threat_score": incident.get("threat_score", incident.get("impact", {}).get("threat_score")),
                    },
                    "zones": zones_data.get("zones", []),
                    "total_population": zones_data.get("total_population_affected", 0),
                    "evacuation_times": zones_data.get("evacuation_times_hours", {}),
                }
                incidents_with_zones.append(incident_result)
            except Exception as e:
                logger.warning(f"Error calculating zones for incident: {str(e)}")
                continue
        
        return {
            "status": "success",
            "incident_count": len(incidents_with_zones),
            "data": incidents_with_zones
        }
        
    except Exception as e:
        logger.error(f"Error fetching zones for all incidents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routes/{incident_id}")
async def get_safe_routes(incident_id: str) -> Dict[str, Any]:
    """
    Get safe evacuation routes for an incident
    
    Args:
        incident_id: Incident identifier
    
    Returns:
        routes_data: {
            routes: [
                {route_id, name, distance_km, safety_score, coordinates}
            ]
        }
    """
    try:
        # Get incident from polling service cache
        polling_service = get_polling_service()
        all_incidents = polling_service.get_incidents()
        
        incident = None
        for inc in all_incidents:
            if (inc.get("data", {}).get("nasa_id") == incident_id or
                inc.get("data", {}).get("usgs_id") == incident_id or
                inc.get("location_name", "").lower() == incident_id.lower()):
                incident = inc
                break
        
        if not incident:
            raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
        
        routes_data = EvacuationZoneService.get_safe_routes(incident)
        
        return {
            "status": "success",
            "data": routes_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating routes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/routes")
async def get_safe_routes_for_coords(
    latitude: float = Query(..., description="Incident latitude"),
    longitude: float = Query(..., description="Incident longitude"),
    event_type: str = Query("other", description="Event type"),
    location_name: str = Query("Location", description="Location name"),
) -> Dict[str, Any]:
    """
    Get safe evacuation routes from coordinates
    
    Args:
        latitude: Incident latitude
        longitude: Incident longitude
        event_type: Type of disaster
        location_name: Location name
    
    Returns:
        routes_data: {
            routes: [
                {route_id, name, direction, distance_km, safety_score, coordinates}
            ]
        }
    """
    try:
        incident = {
            "latitude": latitude,
            "longitude": longitude,
            "event_type": event_type,
            "location_name": location_name,
        }
        
        routes_data = EvacuationZoneService.get_safe_routes(incident)
        
        return {
            "status": "success",
            "data": routes_data
        }
        
    except Exception as e:
        logger.error(f"Error calculating routes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resources/{incident_id}/zone/{zone_number}")
async def get_zone_resources(
    incident_id: str = Path(..., description="Incident identifier"),
    zone_number: int = Path(..., ge=1, le=4, description="Zone number 1-4")
) -> Dict[str, Any]:
    """
    Get resource requirements for evacuating a specific zone
    
    Args:
        incident_id: Incident identifier
        zone_number: Zone number (1-4)
    
    Returns:
        resources: {
            shelters_needed, medical_beds, water, food, vehicles
        }
    """
    try:
        # Get incident from polling service cache
        polling_service = get_polling_service()
        all_incidents = polling_service.get_incidents()
        
        incident = None
        for inc in all_incidents:
            if (inc.get("data", {}).get("nasa_id") == incident_id or
                inc.get("data", {}).get("usgs_id") == incident_id or
                inc.get("location_name", "").lower() == incident_id.lower()):
                incident = inc
                break
        
        if not incident:
            raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
        
        # Calculate zones to get population
        zones_data = EvacuationZoneService.calculate_zones(incident)
        zones = zones_data.get("zones", [])
        
        if not zones or zone_number > len(zones):
            raise HTTPException(status_code=400, detail=f"Zone {zone_number} not found")
        
        zone = zones[zone_number - 1]
        population = zone.get("population_estimate", 0)
        
        resources = EvacuationZoneService.get_zone_resources(zone_number, population)
        
        return {
            "status": "success",
            "incident_id": incident_id,
            "zone_number": zone_number,
            "data": resources
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating resources: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check for zones service"""
    return {
        "status": "ok",
        "service": "evacuation_zones",
        "version": "3.1",
        "features": [
            "zone_calculation",
            "safe_routes",
            "resource_planning",
        ]
    }
