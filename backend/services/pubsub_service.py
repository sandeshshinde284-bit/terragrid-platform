"""
Google Cloud Pub/Sub Service
Publishes real-time disaster events for processing
"""
import logging
import json
import os
from typing import Dict, Any, List
from google.cloud import pubsub_v1
from datetime import datetime

logger = logging.getLogger(__name__)

class PubSubService:
    """Service to publish events to Google Cloud Pub/Sub"""
    
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.topic_id = os.getenv("PUBSUB_TOPIC_ID", "terragrid-events")
        self.publisher = None
        self.enabled = bool(self.project_id)
    
    async def publish_event(self, event: Dict[str, Any]) -> bool:
        """
        Publish a single event to Pub/Sub
        
        Args:
            event: Event dictionary to publish
            
        Returns:
            True if published successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Pub/Sub disabled - skipping publish")
            return False
        
        try:
            if not self.publisher:
                self.publisher = pubsub_v1.PublisherClient()
            
            topic_path = self.publisher.topic_path(self.project_id, self.topic_id)
            
            # Serialize event to JSON
            message_json = json.dumps(event, default=str).encode('utf-8')
            
            # Publish with attributes for filtering
            future = self.publisher.publish(
                topic_path,
                message_json,
                event_type=event.get("event_type", "unknown"),
                severity=event.get("severity", "unknown"),
                source=event.get("source", "unknown")
            )
            
            # Wait for publish to complete
            message_id = future.result(timeout=5.0)
            logger.info(f"✅ Published event to Pub/Sub: {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to publish to Pub/Sub: {str(e)}")
            return False
    
    async def publish_batch(self, events: List[Dict[str, Any]]) -> int:
        """
        Publish multiple events to Pub/Sub
        
        Args:
            events: List of events to publish
            
        Returns:
            Number of successfully published events
        """
        if not self.enabled:
            logger.debug("Pub/Sub disabled - skipping batch publish")
            return 0
        
        success_count = 0
        for event in events:
            if await self.publish_event(event):
                success_count += 1
        
        logger.info(f"✅ Published {success_count}/{len(events)} events to Pub/Sub")
        return success_count
    
    def close(self):
        """Close publisher connection"""
        if self.publisher:
            self.publisher.transport.close()
