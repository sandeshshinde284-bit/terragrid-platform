"""
API Routes for Source of Truth (4-Layer Lineage)
GET /api/incidents/{id}/lineage - Retrieve full lineage chain for an incident
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging

from backend.database import get_db
from backend.services.lineage_tracker import LineageTracker

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.get("/{incident_id}/lineage")
async def get_incident_lineage(
    incident_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Retrieve complete 4-layer lineage chain for an incident
    
    Args:
        incident_id: The ID of the final event
        db: Database session
        
    Returns:
        Dict containing:
        - lineage_id: Chain record ID
        - processing_status: COMPLETE, PARTIAL, or FAILED
        - total_processing_time_ms: Total pipeline processing time
        - created_at: When lineage was created
        - layer_1_raw_ingestion: Raw API response
        - layer_2_validation: Validation checks and errors
        - layer_3_enrichment: Enrichments applied
        - (Layer 4 is the final event itself, queryable separately)
        
    Raises:
        HTTPException: 404 if incident or lineage not found
    """
    try:
        lineage_data = LineageTracker.get_incident_lineage(db, incident_id)
        
        if not lineage_data:
            raise HTTPException(
                status_code=404,
                detail=f"No lineage found for incident {incident_id}"
            )
        
        return {
            "success": True,
            "data": lineage_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving lineage for incident {incident_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving lineage: {str(e)}"
        )


@router.get("/{incident_id}/lineage/summary")
async def get_lineage_summary(
    incident_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a simplified summary of the lineage chain
    
    Returns:
        - incident_id
        - status
        - processing_time_ms
        - layer_count (number of layers successfully processed)
        - errors_found (if any validation errors)
    """
    try:
        lineage_data = LineageTracker.get_incident_lineage(db, incident_id)
        
        if not lineage_data:
            raise HTTPException(
                status_code=404,
                detail=f"No lineage found for incident {incident_id}"
            )
        
        # Count layers
        layer_count = 0
        if lineage_data.get("layer_1_raw_ingestion"):
            layer_count += 1
        if lineage_data.get("layer_2_validation"):
            layer_count += 1
        if lineage_data.get("layer_3_enrichment"):
            layer_count += 1
        if incident_id:  # Layer 4 always exists if we found lineage
            layer_count += 1
        
        # Check for validation errors
        errors_found = False
        if lineage_data.get("layer_2_validation"):
            val_layer = lineage_data["layer_2_validation"]
            if val_layer.get("status") == "FAIL" or val_layer.get("errors"):
                errors_found = True
        
        return {
            "success": True,
            "data": {
                "incident_id": incident_id,
                "status": lineage_data.get("processing_status", "UNKNOWN"),
                "processing_time_ms": lineage_data.get("total_processing_time_ms"),
                "layers_processed": layer_count,
                "total_layers": 4,
                "errors_found": errors_found,
                "created_at": lineage_data.get("created_at")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving lineage summary for incident {incident_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving lineage summary: {str(e)}"
        )
