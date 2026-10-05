"""
API Routes for Features 1 & 2
- Feature 1: Real-Time Data Ingestion
- Feature 2: Impact Analysis
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

from ..services import (
    DataIngestionService, 
    ImpactAnalysisService,
    NASAEONETService,
    GDACSService
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["disaster-data"])

# Feature 1: Real-Time Data Ingestion
@router.get("/ingest/all")
@router.post("/ingest/all")
async def ingest_all_sources(use_mock: bool = Query(False, description="Use mock data for testing")):
    """
    Feature 1: Manually trigger data ingestion from all sources (NASA EONET + GDACS)
    
    Returns:
        - Ingestion results with event counts from each source
        - Total events processed
        - Any errors encountered
    """
    try:
        service = DataIngestionService()
        results = await service.ingest_all_sources(use_mock=use_mock)
        
        return {
            "status": "success",
            "message": f"Ingestion complete: {results['total_events']} events processed",
            "data": results
        }
    except Exception as e:
        logger.error(f"Ingestion error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/nasa-eonet")
async def ingest_nasa_eonet(use_mock: bool = Query(False)):
    """
    Feature 1: Fetch data from NASA EONET API only
    
    Returns:
        - List of natural disaster events
    """
    try:
        events = await NASAEONETService.fetch_events(use_mock=use_mock)
        
        return {
            "status": "success",
            "count": len(events),
            "source": "NASA EONET",
            "data": events
        }
    except Exception as e:
        logger.error(f"NASA EONET error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/gdacs")
async def ingest_gdacs(use_mock: bool = Query(False)):
    """
    Feature 1: Fetch data from GDACS API only
    
    Returns:
        - List of disaster alerts
    """
    try:
        events = await GDACSService.fetch_events(use_mock=use_mock)
        
        return {
            "status": "success",
            "count": len(events),
            "source": "GDACS",
            "data": events
        }
    except Exception as e:
        logger.error(f"GDACS error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Feature 2: Impact Analysis
@router.post("/impact/analyze")
async def analyze_impact(event: Dict[str, Any]):
    """
    Feature 2: Analyze impact of a disaster event
    
    Request body:
        - event_type: Type of disaster (fire, earthquake, flood, etc.)
        - severity: Severity level (low, medium, high, critical)
        - latitude: Event latitude
        - longitude: Event longitude
        - location_name: Location description
    
    Returns:
        - Affected population
        - Affected area in km²
        - Risk score (0-100)
        - Vulnerability assessment
        - Humanitarian impact
        - Recommended actions
    """
    try:
        impact = ImpactAnalysisService.calculate_impact(event)
        
        return {
            "status": "success",
            "location": event.get("location_name", "Unknown"),
            "impact": impact
        }
    except Exception as e:
        logger.error(f"Impact analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/impact/batch")
async def analyze_batch(events: List[Dict[str, Any]]):
    """
    Feature 2: Analyze impact for multiple events
    
    Returns:
        - List of impact analyses
        - Summary statistics
    """
    try:
        impacts = []
        total_population = 0
        total_area = 0
        max_risk = 0
        
        for event in events:
            impact = ImpactAnalysisService.calculate_impact(event)
            impacts.append({
                "location": event.get("location_name"),
                "impact": impact
            })
            
            total_population += impact.get("affected_population", 0)
            total_area += impact.get("affected_area_km2", 0)
            max_risk = max(max_risk, impact.get("risk_score", 0))
        
        return {
            "status": "success",
            "count": len(impacts),
            "summary": {
                "total_affected_population": total_population,
                "total_affected_area_km2": round(total_area, 2),
                "max_risk_score": round(max_risk, 1),
                "critical_events": sum(1 for d in impacts if d["impact"].get("severity_level") == "CRITICAL")
            },
            "data": impacts
        }
    except Exception as e:
        logger.error(f"Batch impact analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Diagnostics
@router.get("/ingest/status")
async def ingestion_status():
    """
    Get status and configuration of data ingestion services
    
    Returns:
        - NASA EONET status
        - GDACS status
        - Pub/Sub status
        - Last ingestion timestamp
    """
    return {
        "status": "operational",
        "services": {
            "nasa_eonet": {
                "enabled": True,
                "description": "NASA Earth Observation Natural Event Tracking",
                "endpoint": "https://eonet.gsfc.nasa.gov/api/v3"
            },
            "gdacs": {
                "enabled": True,
                "description": "Global Disaster Alert & Coordination System",
                "endpoint": "https://www.gdacs.org/api/v1"
            },
            "pubsub": {
                "enabled": True,
                "description": "Google Cloud Pub/Sub for real-time event streaming"
            }
        },
        "features": {
            "feature_1": {
                "name": "Real-Time Data Ingestion",
                "status": "implemented",
                "components": ["NASA EONET", "GDACS", "Pub/Sub", "Database Storage"]
            },
            "feature_2": {
                "name": "Impact Analysis",
                "status": "implemented",
                "metrics": [
                    "Affected Population",
                    "Affected Area (km²)",
                    "Risk Score",
                    "Vulnerability Assessment",
                    "Humanitarian Impact",
                    "Recommended Actions"
                ]
            }
        },
        "polling_interval_minutes": 15,
        "mock_data_available": True,
        "timestamp": datetime.utcnow().isoformat()
    }


# Global mock mode for testing
# [STRICT LIVE] _mock_mode_enabled = True
_mock_mode_enabled = False

@router.get("/config/mock-mode")
async def get_mock_mode():
    """
    Get current mock mode status
    
    Returns:
        - mock_enabled: Whether mock data is currently enabled
    """
    return {
        "mock_enabled": _mock_mode_enabled,
        "description": "Mock data is being used for testing",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/config/mock-mode")
async def set_mock_mode(enabled: bool = Query(True, description="Enable or disable mock data")):
    """
    Enable or disable global mock data mode
    
    This affects all data ingestion endpoints - they will use mock or live data accordingly.
    
    Args:
        enabled: True for mock data, False for live APIs
        
    Returns:
        - Status confirmation
        - New mock mode state
    """
    global _mock_mode_enabled
    _mock_mode_enabled = enabled
    
    return {
        "status": "success",
        "mock_enabled": _mock_mode_enabled,
        "mode": "MOCK DATA (Testing)" if _mock_mode_enabled else "LIVE APIs (Production)",
        "message": f"Switched to {'mock' if enabled else 'live'} data mode",
        "timestamp": datetime.utcnow().isoformat()
    }


# Updated endpoints to use global mock mode
@router.post("/ingest/all-v2")
async def ingest_all_sources_v2():
    """
    Feature 1: Fetch all sources (respects global mock mode)
    
    Uses the globally configured mock mode:
    - If mock mode enabled: Returns mock data
    - If mock mode disabled: Fetches from real APIs
    """
    try:
        service = DataIngestionService()
        results = await service.ingest_all_sources(use_mock=_mock_mode_enabled)
        
        mode_label = "🧪 MOCK DATA" if _mock_mode_enabled else "🌐 LIVE APIs"
        
        return {
            "status": "success",
            "mode": mode_label,
            "message": f"Ingestion complete: {results['total_events']} events processed",
            "data": results
        }
    except Exception as e:
        logger.error(f"Ingestion error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
