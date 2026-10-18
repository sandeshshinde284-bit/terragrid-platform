"""
API routes for PREPARE → RESPONSE preparedness context handoff.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from ..database import get_db
from ..models import IncidentPreparednessContext, Event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/incidents", tags=["preparedness"])


class PreparednessContextCreate(BaseModel):
    """Request to save preparedness context for an incident."""
    city: str
    country: str
    hazard_type: str | None = None
    risk_level: str | None = None
    assessment_at: datetime
    snapshot_json: dict | None = None
    source_metadata_json: dict | None = None
    initiated_by: str
    compatibility_override_reason: str | None = None


class PreparednessContextResponse(BaseModel):
    """Saved preparedness context."""
    id: int
    event_id: int
    city: str
    country: str
    hazard_type: str | None
    risk_level: str | None
    assessment_at: datetime
    initiated_by: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/{incident_id}/preparedness-context", response_model=PreparednessContextResponse)
def save_preparedness_context(
    incident_id: int,
    payload: PreparednessContextCreate,
    db: Session = Depends(get_db),
):
    """
    Save a preparedness assessment snapshot linked to an incident.
    
    Validates:
    - Incident exists (404 if not)
    - Required fields present (422 if not)
    - Idempotency: replaces existing context for this event_id
    
    Does NOT create response tasks. The context is read-only reference data.
    """
    # Validate incident exists
    incident = db.query(Event).filter(Event.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    
    # Validate required fields
    if not payload.initiated_by:
        raise HTTPException(status_code=422, detail="initiated_by is required")
    if not payload.city or not payload.country:
        raise HTTPException(status_code=422, detail="city and country are required")
    
    try:
        # Replace existing context (idempotent)
        existing = db.query(IncidentPreparednessContext).filter(
            IncidentPreparednessContext.event_id == incident_id
        ).first()
        
        if existing:
            existing.city = payload.city
            existing.country = payload.country
            existing.hazard_type = payload.hazard_type
            existing.risk_level = payload.risk_level
            existing.assessment_at = payload.assessment_at
            existing.snapshot_json = payload.snapshot_json
            existing.source_metadata_json = payload.source_metadata_json
            existing.initiated_by = payload.initiated_by
            existing.compatibility_override_reason = payload.compatibility_override_reason
            existing.updated_at = datetime.utcnow()
            context = existing
        else:
            context = IncidentPreparednessContext(
                event_id=incident_id,
                city=payload.city,
                country=payload.country,
                hazard_type=payload.hazard_type,
                risk_level=payload.risk_level,
                assessment_at=payload.assessment_at,
                snapshot_json=payload.snapshot_json,
                source_metadata_json=payload.source_metadata_json,
                initiated_by=payload.initiated_by,
                compatibility_override_reason=payload.compatibility_override_reason,
            )
            db.add(context)
        
        db.commit()
        db.refresh(context)
        logger.info(f"Saved preparedness context for incident {incident_id} by {payload.initiated_by}")
        return context
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving preparedness context: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save context")


@router.get("/{incident_id}/preparedness-context", response_model=PreparednessContextResponse | None)
def get_preparedness_context(
    incident_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve preparedness context for an incident.
    Returns None (empty response) if no context exists.
    """
    # Validate incident exists
    incident = db.query(Event).filter(Event.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    
    context = db.query(IncidentPreparednessContext).filter(
        IncidentPreparednessContext.event_id == incident_id
    ).first()
    
    return context
