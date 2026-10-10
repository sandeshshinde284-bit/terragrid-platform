"""
Feature 3: Background Polling Service
Auto-refreshes incident data every 15 minutes using APScheduler
"""
import logging
import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import json

logger = logging.getLogger(__name__)

class BackgroundPollingService:
    """Manages background polling of disaster data"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.last_refresh: Optional[datetime] = None
        self.last_incident_count: int = 0
        self.current_incidents: List[Dict[str, Any]] = []
        self.incident_history: List[Dict[str, Any]] = []
        self.polling_enabled: bool = True
        self.is_running: bool = False
        
        # Pull interval from .env (defaults to 15 if not set)
        env_interval = os.getenv("POLLING_INTERVAL_MINUTES", "15")
        try:
            self.refresh_interval_minutes = int(env_interval)
        except ValueError:
            logger.warning(f"Invalid POLLING_INTERVAL_MINUTES '{env_interval}'. Defaulting to 15.")
            self.refresh_interval_minutes = 15
    
    def start(self, data_ingestion_service) -> bool:
        """
        Start background polling service
        
        Args:
            data_ingestion_service: The DataIngestionService to use for fetching
            
        Returns:
            True if started successfully
        """
        if self.is_running:
            logger.warning("Polling service already running")
            return False
        
        try:
            self.data_ingestion_service = data_ingestion_service
            
            # Schedule the polling job to run every N minutes
            self.scheduler.add_job(
                func=self._polling_job,
                trigger=IntervalTrigger(minutes=self.refresh_interval_minutes),
                id="disaster_data_polling",
                name="Fetch disaster data every 15 minutes",
                replace_existing=True,
                max_instances=1,  # Only one instance running at a time
            )
            
            self.scheduler.start()
            self.is_running = True
            
            # Run first refresh immediately
            asyncio.create_task(self._async_polling_job())
            
            logger.info(f"Background polling service started (interval: {self.refresh_interval_minutes} min)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start polling service: {str(e)}")
            return False
    
    def stop(self) -> bool:
        """Stop background polling service"""
        if not self.is_running:
            logger.warning("Polling service not running")
            return False
        
        try:
            self.scheduler.shutdown()
            self.is_running = False
            self.polling_enabled = False
            logger.info("Background polling service stopped")
            return True
        except Exception as e:
            logger.error(f"Error stopping polling service: {str(e)}")
            return False
    
    def _polling_job(self):
        """
        Background job that runs periodically
        Wrapper to handle async operations in sync scheduler
        """
        try:
            # Create a new event loop for this thread if needed
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._async_polling_job())
            loop.close()
        except Exception as e:
            logger.error(f"Polling job error: {str(e)}")
    
    async def _async_polling_job(self):
        """Actual async polling logic"""
        if not self.polling_enabled:
            logger.debug("Polling disabled")
            return

        try:
            logger.info("🔄 Background polling: Fetching latest incidents...")

            # Fetch latest incidents
            from backend.database import SessionLocal

            with SessionLocal() as db_session:
                result = await self.data_ingestion_service.ingest_all_sources(
                    use_mock=False, 
                    db_session=db_session
                )

            new_incidents = result.get("events", [])
            old_count = self.last_incident_count
            new_count = len(new_incidents)
            
            # Track changes
            changes = self._detect_changes(new_incidents)
            
            # Update state
            self.last_incident_count = new_count
            self.last_refresh = datetime.utcnow()
            
            # Store in history
            self._update_history(result)
            
            # Log summary
            new_val = changes['new']
            updated_val = changes['updated']
            removed_val = changes['removed']
            logger.info(
                f"Polling complete: {new_count} incidents "
                f"({new_val} new, {updated_val} updated, {removed_val} removed)"
            )
            
            # Log source breakdown
            sources = result.get("sources", {})
            for source, info in sources.items():
                logger.info(f"   {source}: {info.get('count', 0)} events")
            
            # FEATURE 4: Broadcast real-time update via WebSocket
            try:
                from backend.services.websocket import manager
                # Only broadcast if there are actual active connections to save overhead
                if len(manager.active_connections) > 0:
                    logger.info("Broadcasting updates via WebSocket...")
                    await manager.broadcast_json({
                        "type": "incidents_polled",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": {
                            "total_events": new_count,
                            "changes": changes,
                            "events": new_incidents[:50] # Send top 50 to avoid huge payloads
                        }
                    })
            except Exception as ws_e:
                logger.error(f"WebSocket broadcast failed: {str(ws_e)}")
            
        except Exception as e:
            logger.error(f"Polling job failed: {str(e)}")
    
    def _detect_changes(self, new_incidents: List[Dict]) -> Dict[str, int]:
        """
        Detect new, updated, and removed incidents
        
        Returns:
            Dict with keys: new, updated, removed
        """
        changes = {"new": 0, "updated": 0, "removed": 0}
        
        try:
            old_ids = {self._get_incident_id(i) for i in self.current_incidents}
            new_ids = {self._get_incident_id(i) for i in new_incidents}
            
            changes["new"] = len(new_ids - old_ids)
            changes["removed"] = len(old_ids - new_ids)
            changes["updated"] = len(new_ids & old_ids)
            
            # Update current state
            self.current_incidents = new_incidents
            
        except Exception as e:
            logger.error(f"Error detecting changes: {str(e)}")
        
        return changes
    
    def _get_incident_id(self, incident: Dict) -> str:
        """Get unique ID for an incident"""
        return incident.get("data", {}).get("nasa_id") or \
               incident.get("data", {}).get("usgs_id") or \
               incident.get("data", {}).get("noaa_id") or \
               f"{incident.get('location_name')}_{incident.get('event_type')}"
    
    def _update_history(self, result: Dict[str, Any]):
        """Store polling results in history"""
        try:
            history_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "total_events": result.get("total_events", 0),
                "sources": result.get("sources", {}),
                "errors": result.get("errors", []),
            }
            self.incident_history.append(history_entry)
            
            # Keep only last 100 history entries
            if len(self.incident_history) > 100:
                self.incident_history = self.incident_history[-100:]
            
        except Exception as e:
            logger.error(f"Error updating history: {str(e)}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get polling service status"""
        return {
            "is_running": self.is_running,
            "polling_enabled": self.polling_enabled,
            "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None,
            "refresh_interval_minutes": self.refresh_interval_minutes,
            "current_incident_count": len(self.current_incidents),
            "last_incident_count": self.last_incident_count,
            "history_length": len(self.incident_history),
        }
    
    def get_incidents(self) -> List[Dict[str, Any]]:
        """Get current incidents from polling"""
        return self.current_incidents
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent polling history"""
        return self.incident_history[-limit:]
    
    def enable_polling(self):
        """Enable polling"""
        self.polling_enabled = True
        logger.info("Polling enabled")
    
    def disable_polling(self):
        """Disable polling (without stopping scheduler)"""
        self.polling_enabled = False
        logger.info("Polling disabled")
    
    def set_interval(self, minutes: int):
        """Change polling interval"""
        if minutes < 1 or minutes > 1440:  # Min 1 min, max 24 hours
            logger.error(f"Invalid interval: {minutes}. Must be between 1 and 1440 minutes")
            return False
        
        self.refresh_interval_minutes = minutes
        
        if self.is_running:
            # Reschedule the job
            self.scheduler.remove_job("disaster_data_polling")
            self.scheduler.add_job(
                func=self._polling_job,
                trigger=IntervalTrigger(minutes=minutes),
                id="disaster_data_polling",
                name=f"Fetch disaster data every {minutes} minutes",
                replace_existing=True,
            )
        
        logger.info(f"Polling interval changed to {minutes} minutes")
        return True


# Global instance
_polling_service: Optional[BackgroundPollingService] = None

def get_polling_service() -> BackgroundPollingService:
    """Get or create global polling service instance"""
    global _polling_service
    if _polling_service is None:
        _polling_service = BackgroundPollingService()
    return _polling_service
