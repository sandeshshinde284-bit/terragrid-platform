"""
API Routes for Feature 3: Background Polling
- Auto-refresh incidents every 15 minutes
- Check polling status
- Control polling on/off
"""
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from typing import Dict, Any
import logging

from ..services.polling import get_polling_service
from ..services.data_ingestion import DataIngestionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["polling"])

# Feature 3: Background Polling Management

@router.get("/polling/status")
async def get_polling_status() -> Dict[str, Any]:
    """
    Get current status of background polling service
    
    Returns:
        - is_running: Whether polling service is active
        - polling_enabled: Whether polling is enabled
        - last_refresh: Timestamp of last refresh
        - refresh_interval_minutes: Current polling interval
        - current_incident_count: Number of incidents in current refresh
        - last_incident_count: Number of incidents in last refresh
    """
    try:
        service = get_polling_service()
        return {
            "status": "success",
            "data": service.get_status()
        }
    except Exception as e:
        logger.error(f"Error getting polling status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/polling/start")
async def start_polling() -> Dict[str, Any]:
    """
    Start background polling service
    
    Returns:
        - success: Whether polling started successfully
    """
    try:
        service = get_polling_service()
        data_ingestion = DataIngestionService()
        
        if service.start(data_ingestion):
            return {
                "status": "success",
                "message": "Background polling started",
                "data": service.get_status()
            }
        else:
            raise HTTPException(status_code=400, detail="Polling already running")
    except Exception as e:
        logger.error(f"Error starting polling: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/polling/stop")
async def stop_polling() -> Dict[str, Any]:
    """Stop background polling service"""
    try:
        service = get_polling_service()
        
        if service.stop():
            return {
                "status": "success",
                "message": "Background polling stopped",
                "data": service.get_status()
            }
        else:
            raise HTTPException(status_code=400, detail="Polling not running")
    except Exception as e:
        logger.error(f"Error stopping polling: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/polling/enable")
async def enable_polling() -> Dict[str, Any]:
    """Enable polling (without restarting service)"""
    try:
        service = get_polling_service()
        service.enable_polling()
        
        return {
            "status": "success",
            "message": "Polling enabled",
            "data": service.get_status()
        }
    except Exception as e:
        logger.error(f"Error enabling polling: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/polling/disable")
async def disable_polling() -> Dict[str, Any]:
    """Disable polling (keep service running but pause fetching)"""
    try:
        service = get_polling_service()
        service.disable_polling()
        
        return {
            "status": "success",
            "message": "Polling disabled",
            "data": service.get_status()
        }
    except Exception as e:
        logger.error(f"Error disabling polling: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/polling/refresh")
async def manual_refresh(use_mock: bool = Query(False)) -> Dict[str, Any]:
    """
    Manually trigger immediate refresh (regardless of polling schedule)
    
    Args:
        use_mock: Whether to use mock data
        
    Returns:
        - Refreshed incident data and counts
    """
    try:
        service = DataIngestionService()
        result = await service.ingest_all_sources(use_mock=use_mock)
        
        return {
            "status": "success",
            "message": f"Manual refresh complete: {result['total_events']} events",
            "data": result
        }
    except Exception as e:
        logger.error(f"Error during manual refresh: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/polling/set-interval")
async def set_polling_interval(minutes: int = Query(..., ge=1, le=1440)) -> Dict[str, Any]:
    """
    Change polling interval
    
    Args:
        minutes: New interval in minutes (1-1440)
        
    Returns:
        - Updated polling status
    """
    try:
        service = get_polling_service()
        
        if service.set_interval(minutes):
            return {
                "status": "success",
                "message": f"Polling interval set to {minutes} minutes",
                "data": service.get_status()
            }
        else:
            raise HTTPException(status_code=400, detail=f"Invalid interval: {minutes}")
    except Exception as e:
        logger.error(f"Error setting polling interval: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/polling/incidents")
async def get_polling_incidents() -> Dict[str, Any]:
    """Get current incidents from latest polling refresh"""
    try:
        service = get_polling_service()
        incidents = service.get_incidents()
        
        return {
            "status": "success",
            "data": {
                "count": len(incidents),
                "incidents": incidents,
                "last_refresh": service.get_status()["last_refresh"]
            }
        }
    except Exception as e:
        logger.error(f"Error getting polling incidents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/polling/history")
async def get_polling_history(limit: int = Query(10, ge=1, le=100)) -> Dict[str, Any]:
    """
    Get polling history (recent refresh attempts)
    
    Args:
        limit: Number of recent entries to return (1-100)
        
    Returns:
        - List of polling attempts with timestamps and event counts
    """
    try:
        service = get_polling_service()
        history = service.get_history(limit)
        
        return {
            "status": "success",
            "data": {
                "count": len(history),
                "history": history
            }
        }
    except Exception as e:
        logger.error(f"Error getting polling history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
