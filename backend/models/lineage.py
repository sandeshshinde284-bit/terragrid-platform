"""
4-Layer Lineage Models for Source of Truth Feature
Tracks data transformation through all 4 layers:
- Layer 1: Raw ingestion
- Layer 2: Validation
- Layer 3: Enrichment
- Layer 4: Analysis/Storage
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .base import BaseModel


class RawEvent(BaseModel):
    """
    Layer 1: Raw Ingestion
    Stores untouched API response from data sources
    """
    __tablename__ = "raw_events"
    
    # Source metadata
    source = Column(String(50), nullable=False)  # nasa_eonet, gdacs, usgs, etc
    
    # Raw data - exactly as received from API (never modified)
    api_response = Column(JSONB, nullable=False)  # Full untouched API response
    http_status_code = Column(Integer, nullable=False)  # 200, 404, 500, etc
    
    # Tracking
    fetched_at = Column(DateTime, nullable=False)  # When API was called
    
    def __repr__(self):
        return f"<RawEvent {self.id}: {self.source} (HTTP {self.http_status_code})>"


class ValidationLog(BaseModel):
    """
    Layer 2: Validation
    Logs validation checks and results
    """
    __tablename__ = "validation_log"
    
    # Foreign key to raw event
    raw_event_id = Column(Integer, ForeignKey("raw_events.id"), nullable=False)
    
    # Validation results
    validation_status = Column(String(20), nullable=False)  # PASS or FAIL
    errors = Column(JSONB, nullable=True)  # {field: error_message, ...}
    
    # Metadata
    validator_version = Column(String(20), nullable=False)  # Which validator ran
    validated_at = Column(DateTime, nullable=False)
    
    # Index for foreign key lookups
    __table_args__ = (
        Index("ix_validation_raw_event", "raw_event_id"),
    )
    
    def __repr__(self):
        return f"<ValidationLog {self.id}: {self.validation_status}>"


class EnrichmentLog(BaseModel):
    """
    Layer 3: Enrichment
    Logs each transformation/enrichment applied
    """
    __tablename__ = "enrichment_log"
    
    # Foreign key to validation
    validation_log_id = Column(Integer, ForeignKey("validation_log.id"), nullable=False)
    
    # Enrichment type
    enrichment_type = Column(String(50), nullable=False)  # geocoding, risk_score, etc
    enrichment_service = Column(String(50), nullable=False)  # Which service applied it
    
    # Before and after values
    original_value = Column(JSONB, nullable=True)  # Before enrichment
    enriched_value = Column(JSONB, nullable=False)  # After enrichment
    
    # Metadata
    enriched_at = Column(DateTime, nullable=False)
    
    # Index for foreign key lookups
    __table_args__ = (
        Index("ix_enrichment_validation", "validation_log_id"),
    )
    
    def __repr__(self):
        return f"<EnrichmentLog {self.id}: {self.enrichment_type}>"


class LineageChain(BaseModel):
    """
    Glue Table: Links all 4 layers together for full audit trail
    One record per incident = complete lineage chain
    """
    __tablename__ = "lineage_chain"
    
    # Foreign keys to all 4 layers
    raw_event_id = Column(Integer, ForeignKey("raw_events.id"), nullable=False)
    validation_log_id = Column(Integer, ForeignKey("validation_log.id"), nullable=False)
    enrichment_log_id = Column(Integer, ForeignKey("enrichment_log.id"), nullable=False)
    final_event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    
    # Metadata
    processing_status = Column(String(20), nullable=False)  # COMPLETE, PARTIAL, FAILED
    total_processing_time_ms = Column(Integer, nullable=True)  # Total time through all layers
    
    # Composite index for lookups
    __table_args__ = (
        Index("ix_lineage_final_event", "final_event_id"),
        Index("ix_lineage_raw_event", "raw_event_id"),
    )
    
    def __repr__(self):
        return f"<LineageChain {self.id}: {self.processing_status}>"
