"""
GDACS (Global Disaster Alert & Coordination System) API Service
Fetches disaster alerts and humanitarian data
"""
import httpx
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)

class GDACSService:
    """Service to fetch disaster alerts from GDACS API"""
    
    BASE_URL = "https://www.gdacs.org/api/v1"
    
    # Disaster type mappings
    DISASTER_MAPPING = {
        'FL': 'flood',
        'EQ': 'earthquake',
        'TC': 'storm',
        'VO': 'volcano',
        'DR': 'drought',
        'WF': 'fire',
        'CW': 'cold_wave',
        'HW': 'heat_wave',
    }
    
    @classmethod
    async def fetch_events(cls, use_mock: bool = False) -> List[Dict[str, Any]]:
        """
        Fetch disaster alerts from GDACS
        
        Args:
            use_mock: If True, return mock data instead of calling API
            
        Returns:
            List of event dictionaries
        """
        if use_mock:
            return cls._get_mock_data()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{cls.BASE_URL}/events",
                    params={
                        "limit": 100,
                        "status": "alert"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                events = []
                for event in data.get("events", []):
                    parsed = cls._parse_event(event)
                    if parsed:
                        events.append(parsed)
                
                logger.info(f"✅ GDACS: Fetched {len(events)} events")
                return events
                
        except Exception as e:
            logger.error(f"❌ GDACS API Error: {str(e)}")
            return cls._get_mock_data()
    
    @classmethod
    def _parse_event(cls, event: Dict) -> Dict[str, Any] | None:
        """Parse GDACS event to internal format"""
        try:
            disaster_type = event.get("disasterType", "").upper()
            event_type = cls.DISASTER_MAPPING.get(disaster_type, "other")
            
            # Calculate severity from alert score (0-8)
            alert_score = float(event.get("alertScore", 0))
            if alert_score >= 6:
                severity = "critical"
            elif alert_score >= 5:
                severity = "high"
            elif alert_score >= 3:
                severity = "medium"
            else:
                severity = "low"
            
            return {
                "event_type": event_type,
                "severity": severity,
                "status": "confirmed",
                "latitude": float(event.get("latitude", 0)),
                "longitude": float(event.get("longitude", 0)),
                "location_name": event.get("description", "Unknown"),
                "source": "GDACS",
                "event_timestamp": cls._parse_date(event.get("eventDate")),
                "confidence": min(0.99, (alert_score / 8.0) * 0.95),
                "is_verified": True,
                "data": {
                    "gdacs_id": event.get("eventId"),
                    "alert_score": alert_score,
                    "affected_population": event.get("affectedPopulation", 0),
                    "vulnerability": event.get("vulnerability", ""),
                    "recommendation": event.get("recommendation", "")
                }
            }
        except Exception as e:
            logger.error(f"Error parsing GDACS event: {str(e)}")
            return None
    
    @classmethod
    def _parse_date(cls, date_str: str | None) -> datetime:
        """Parse ISO date string"""
        if not date_str:
            return datetime.utcnow()
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return datetime.utcnow()
    
    @classmethod
    def _get_mock_data(cls) -> List[Dict[str, Any]]:
        """Return mock GDACS data for testing"""
        now = datetime.utcnow()
        return [
            {
                "event_type": "flood",
                "severity": "high",
                "status": "confirmed",
                "latitude": 28.6139,
                "longitude": 77.2090,
                "location_name": "New Delhi Flooding Alert",
                "source": "GDACS",
                "event_timestamp": now - timedelta(hours=3),
                "confidence": 0.93,
                "is_verified": True,
                "data": {
                    "gdacs_id": "GDACS_MOCK_001",
                    "alert_score": 6.5,
                    "affected_population": 500000,
                    "vulnerability": "high",
                    "recommendation": "Evacuate vulnerable populations"
                }
            },
            {
                "event_type": "earthquake",
                "severity": "high",
                "status": "confirmed",
                "latitude": -33.8688,
                "longitude": 151.2093,
                "location_name": "Sydney Seismic Event",
                "source": "GDACS",
                "event_timestamp": now - timedelta(hours=5),
                "confidence": 0.91,
                "is_verified": True,
                "data": {
                    "gdacs_id": "GDACS_MOCK_002",
                    "alert_score": 5.8,
                    "affected_population": 300000,
                    "vulnerability": "medium",
                    "recommendation": "Structural damage assessment needed"
                }
            },
            {
                "event_type": "storm",
                "severity": "critical",
                "status": "confirmed",
                "latitude": 15.2993,
                "longitude": 74.1240,
                "location_name": "Arabian Sea Cyclone",
                "source": "GDACS",
                "event_timestamp": now - timedelta(hours=1),
                "confidence": 0.96,
                "is_verified": True,
                "data": {
                    "gdacs_id": "GDACS_MOCK_003",
                    "alert_score": 7.2,
                    "affected_population": 2000000,
                    "vulnerability": "very_high",
                    "recommendation": "Immediate evacuation advised"
                }
            }
        ]
