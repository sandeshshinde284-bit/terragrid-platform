"""
GDACS (Global Disaster Alert & Coordination System) API Service
Fetches disaster alerts and humanitarian data
"""
import httpx
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class GDACSService:
    """Service to fetch disaster alerts from official GDACS GeoJSON API"""
    
    BASE_URL = "https://www.gdacs.org/gdacsapi/api/Events/geteventlist/latest"
    
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
        Fetch disaster alerts from GDACS GeoJSON endpoint
        
        Args:
            use_mock: If True, return mock data instead of calling API
            
        Returns:
            List of event dictionaries
        """
        if use_mock:
            logger.info(" GDACS: 🧪 MOCK MODE ENABLED via .env")
            return cls._get_mock_data()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(cls.BASE_URL)
                response.raise_for_status()
                try:
                    data = response.json()
                except Exception as json_err:
                    logger.warning(f"GDACS returned non-JSON response. Returning empty list.")
                    return []
                
                events = []
                features = data.get("features", [])
                for feature in features:
                    parsed = cls._parse_event(feature)
                    if parsed:
                        events.append(parsed)
                
                logger.info(f" GDACS: Fetched {len(events)} events")
                return events
                
        except Exception as e:
            logger.error(f" GDACS API Error: {str(e)}")
            return []
    
    @classmethod
    def _parse_event(cls, feature: Dict) -> Dict[str, Any] | None:
        """Parse GDACS GeoJSON feature to internal format"""
        try:
            properties = feature.get("properties", {})
            geometry = feature.get("geometry", {})
            
            disaster_type = properties.get("eventtype", "").upper()
            event_type = cls.DISASTER_MAPPING.get(disaster_type, "other")
            
            # Map severity from alertlevel string
            alert_level = properties.get("alertlevel", "").lower()
            if alert_level == "red":
                severity = "critical"
                confidence = 0.95
            elif alert_level == "orange":
                severity = "high"
                confidence = 0.85
            elif alert_level == "green":
                severity = "low"
                confidence = 0.70
            else:
                severity = "medium"
                confidence = 0.60
                
            coordinates = geometry.get("coordinates", [0, 0])
            if len(coordinates) >= 2:
                lon, lat = coordinates[0], coordinates[1]
            else:
                return None
                
            # Construct a descriptive name combining event name and country
            event_name = properties.get("eventname", "")
            country = properties.get("country", "")
            if event_name and country:
                location_name = f"{event_name}, {country}"
            elif country:
                location_name = country
            elif event_name:
                location_name = event_name
            else:
                location_name = "Unknown GDACS Location"
            
            return {
                "event_type": event_type,
                "severity": severity,
                "status": "active",
                "latitude": float(lat),
                "longitude": float(lon),
                "location_name": location_name,
                "source": "GDACS",
                "event_timestamp": cls._parse_date(properties.get("fromdate")),
                "confidence": confidence,
                "is_verified": True,
                "data": {
                    "gdacs_id": properties.get("eventid"),
                    "episode_id": properties.get("episodeid"),
                    "alert_level": alert_level,
                    "event_name": event_name,
                    "country": country,
                    "url": properties.get("url")
                }
            }
        except Exception as e:
            logger.error(f"Error parsing GDACS GeoJSON feature: {str(e)}")
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
        pass
