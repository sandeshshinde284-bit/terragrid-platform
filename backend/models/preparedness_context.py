"""
Preparedness context snapshot linked to an incident.
Records PREPARE phase preparedness assessments for RESPONSE phase decision support.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .base import BaseModel


class IncidentPreparednessContext(BaseModel):
    """Snapshot of preparedness assessment linked to an incident."""
    __tablename__ = "incident_preparedness_contexts"

    # Core link (nullable for Phase 2: allows saving assessment without incident for later linking)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True, index=True)
    
    # Location & hazard from PREPARE
    city = Column(String(120), nullable=False)
    country = Column(String(120), nullable=False)
    hazard_type = Column(String(50), nullable=True)  # 'fire', 'flood', 'earthquake', etc.
    risk_level = Column(String(20), nullable=True)  # 'low', 'medium', 'high', 'critical'
    
    # Assessment timing
    assessment_at = Column(DateTime, nullable=False)  # When PREPARE forecast was made
    
    # Full snapshot (checklist items + agencies)
    snapshot_json = Column(JSONB, nullable=True)  # {actions: [], agencies: [], ...}
    source_metadata_json = Column(JSONB, nullable=True)  # {ai_available, is_fallback, is_mock_demo}
    
    # Audit trail
    initiated_by = Column(String(120), nullable=False)  # Officer name (self-declared)
    compatibility_override_reason = Column(Text, nullable=True)  # If hazard mismatched
    
    def __repr__(self):
        return f"<IncidentPreparednessContext {self.id}: event {self.event_id} ({self.city}, {self.hazard_type})>"
