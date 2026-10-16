"""
Lineage Service - Manages 4-layer data lineage tracking
Coordinates raw ingestion → validation → enrichment → final storage
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import time

logger = logging.getLogger(__name__)


class LineageTracker:
    """
    Tracks incident data through all 4 layers
    """
    
    @staticmethod
    def log_raw_event(db_session, source: str, api_response: Dict[str, Any], http_status_code: int):
        """
        Layer 1: Log raw API response
        
        Args:
            db_session: SQLAlchemy session
            source: API source (nasa_eonet, gdacs, etc)
            api_response: Full API response (untouched)
            http_status_code: HTTP status code
            
        Returns:
            raw_event record id
        """
        try:
            from backend.models.lineage import RawEvent
            
            raw_event = RawEvent(
                source=source,
                api_response=api_response,
                http_status_code=http_status_code,
                fetched_at=datetime.utcnow()
            )
            
            db_session.add(raw_event)
            db_session.flush()  # Get ID without committing
            
            logger.info(f"LineageTracker: Layer 1 - Raw event logged (ID: {raw_event.id})")
            return raw_event.id
            
        except Exception as e:
            logger.error(f"LineageTracker: Error logging raw event ({type(e).__name__}: {e})")
            return None
    
    @staticmethod
    def log_validation(
        db_session,
        raw_event_id: int,
        validation_status: str,
        errors: Optional[List[Dict[str, str]]] = None,
        validator_version: str = "v1.0"
    ):
        """
        Layer 2: Log validation results
        
        Args:
            db_session: SQLAlchemy session
            raw_event_id: ID of raw event being validated
            validation_status: PASS or FAIL
            errors: List of validation errors (if any)
            validator_version: Version of validation rules
            
        Returns:
            validation_log record id
        """
        try:
            from backend.models.lineage import ValidationLog
            
            error_dict = {}
            if errors:
                for error in errors:
                    error_dict.update(error)
            
            validation_log = ValidationLog(
                raw_event_id=raw_event_id,
                validation_status=validation_status,
                errors=error_dict if error_dict else None,
                validator_version=validator_version,
                validated_at=datetime.utcnow()
            )
            
            db_session.add(validation_log)
            db_session.flush()
            
            logger.info(f"LineageTracker: Layer 2 - Validation logged (ID: {validation_log.id}, Status: {validation_status})")
            return validation_log.id
            
        except Exception as e:
            logger.error(f"LineageTracker: Error logging validation ({type(e).__name__}: {e})")
            return None
    
    @staticmethod
    def log_enrichment(
        db_session,
        validation_log_id: int,
        enrichment_type: str,
        enrichment_service: str,
        original_value: Any,
        enriched_value: Any
    ):
        """
        Layer 3: Log enrichment operation
        
        Args:
            db_session: SQLAlchemy session
            validation_log_id: ID of validation log
            enrichment_type: Type of enrichment (geocoding, risk_score, etc)
            enrichment_service: Which service performed enrichment
            original_value: Value before enrichment
            enriched_value: Value after enrichment
            
        Returns:
            enrichment_log record id
        """
        try:
            from backend.models.lineage import EnrichmentLog
            
            enrichment_log = EnrichmentLog(
                validation_log_id=validation_log_id,
                enrichment_type=enrichment_type,
                enrichment_service=enrichment_service,
                original_value=original_value,
                enriched_value=enriched_value,
                enriched_at=datetime.utcnow()
            )
            
            db_session.add(enrichment_log)
            db_session.flush()
            
            logger.info(f"LineageTracker: Layer 3 - Enrichment logged (ID: {enrichment_log.id}, Type: {enrichment_type})")
            return enrichment_log.id
            
        except Exception as e:
            logger.error(f"LineageTracker: Error logging enrichment ({type(e).__name__}: {e})")
            return None
    
    @staticmethod
    def create_lineage_chain(
        db_session,
        raw_event_id: int,
        validation_log_id: int,
        enrichment_log_id: int,
        final_event_id: int,
        processing_status: str = "COMPLETE",
        total_processing_time_ms: Optional[int] = None
    ):
        """
        Layer 4: Create lineage chain linking all 4 layers
        
        Args:
            db_session: SQLAlchemy session
            raw_event_id: ID of raw event (Layer 1)
            validation_log_id: ID of validation log (Layer 2)
            enrichment_log_id: ID of enrichment log (Layer 3)
            final_event_id: ID of final event (Layer 4)
            processing_status: COMPLETE, PARTIAL, or FAILED
            total_processing_time_ms: Total time through pipeline
            
        Returns:
            lineage_chain record id
        """
        try:
            from backend.models.lineage import LineageChain
            
            lineage_chain = LineageChain(
                raw_event_id=raw_event_id,
                validation_log_id=validation_log_id,
                enrichment_log_id=enrichment_log_id,
                final_event_id=final_event_id,
                processing_status=processing_status,
                total_processing_time_ms=total_processing_time_ms
            )
            
            db_session.add(lineage_chain)
            db_session.flush()
            
            logger.info(f"LineageTracker: Layer 4 - Lineage chain created (ID: {lineage_chain.id})")
            return lineage_chain.id
            
        except Exception as e:
            logger.error(f"LineageTracker: Error creating lineage chain ({type(e).__name__}: {e})")
            return None
    
    @staticmethod
    def get_incident_lineage(db_session, final_event_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve complete lineage chain for an incident
        
        Args:
            db_session: SQLAlchemy session
            final_event_id: ID of final event
            
        Returns:
            Dict with all 4 layers or None
        """
        try:
            from backend.models.lineage import LineageChain, RawEvent, ValidationLog, EnrichmentLog
            
            # Get lineage chain
            lineage = db_session.query(LineageChain).filter(
                LineageChain.final_event_id == final_event_id
            ).first()
            
            if not lineage:
                logger.warning(f"LineageTracker: No lineage found for event {final_event_id}")
                return None
            
            # Get all 4 layers
            raw_event = db_session.query(RawEvent).filter(RawEvent.id == lineage.raw_event_id).first()
            validation_log = db_session.query(ValidationLog).filter(ValidationLog.id == lineage.validation_log_id).first()
            enrichment_log = db_session.query(EnrichmentLog).filter(EnrichmentLog.id == lineage.enrichment_log_id).first()
            
            return {
                "lineage_id": lineage.id,
                "processing_status": lineage.processing_status,
                "total_processing_time_ms": lineage.total_processing_time_ms,
                "created_at": lineage.created_at,
                "layer_1_raw_ingestion": {
                    "id": raw_event.id,
                    "source": raw_event.source,
                    "http_status_code": raw_event.http_status_code,
                    "fetched_at": raw_event.fetched_at,
                    "api_response": raw_event.api_response
                } if raw_event else None,
                "layer_2_validation": {
                    "id": validation_log.id,
                    "status": validation_log.validation_status,
                    "errors": validation_log.errors,
                    "validator_version": validation_log.validator_version,
                    "validated_at": validation_log.validated_at
                } if validation_log else None,
                "layer_3_enrichment": {
                    "id": enrichment_log.id,
                    "enrichment_type": enrichment_log.enrichment_type,
                    "enrichment_service": enrichment_log.enrichment_service,
                    "original_value": enrichment_log.original_value,
                    "enriched_value": enrichment_log.enriched_value,
                    "enriched_at": enrichment_log.enriched_at
                } if enrichment_log else None
            }
            
        except Exception as e:
            logger.error(f"LineageTracker: Error retrieving incident lineage ({type(e).__name__}: {e})")
            return None
