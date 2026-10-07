"""
USGS Earthquake Hazards Program API Service
Fetches real-time earthquake data from USGS
"""
import httpx
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class USGSEarthquakeService:
    """Service to fetch earthquake events from USGS API"""
    
    BASE_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary"
    
    MAGNITUDE_TO_SEVERITY = {
        'micro': 'low',      # < 2.0
        'minor': 'low',      # 2.0 - 3.0
        'light': 'low',      # 3.0 - 4.0
        'moderate': 'medium', # 4.0 - 5.0
        'strong': 'high',    # 5.0 - 6.0
        'major': 'high',     # 6.0 - 7.0
        'great': 'critical', # > 7.0
    }
    
    @classmethod
    async def fetch_events(cls, use_mock: bool = False, days: int = 7, min_magnitude: float = 4.0) -> List[Dict[str, Any]]:
        """
        Fetch recent earthquake events from USGS
        
        Args:
            use_mock: If True, return mock data instead of calling API
            days: Number of days to look back (default 7)
            min_magnitude: Minimum magnitude to include (default 4.0 to filter noise)
            
        Returns:
            List of earthquake event dictionaries
        """
        # 12-Factor App: Strict Environment-Driven Mock Guard
        if use_mock:
            logger.info(" USGS Earthquakes: 🧪 MOCK MODE ENABLED via .env")
            try:
                import json
                from pathlib import Path
                mock_path = Path(__file__).parent.parent / "data" / "mocks" / "usgs_earthquake.json"
                with open(mock_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load USGS mock: {e}")
                return []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # USGS provides different feeds by time period and magnitude.
                # '4.5_day.geojson' hits the perfect sweet spot: 
                # - Daily feed (fast updates, less bloat than week/month)
                # - Mag 4.5+ (threshold where structural damage starts, skipping micro-quakes)
                
                response = await client.get(
                    f"{cls.BASE_URL}/4.5_day.geojson",
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                events = []
                for feature in data.get("features", []):
                    # We can remove manual min_magnitude filtering because 
                    # the 4.5+ USGS feed natively enforces the threshold.
                    parsed = cls._parse_event(feature)
                    if parsed:
                        events.append(parsed)
                
                logger.info(f" USGS Earthquakes: Fetched {len(events)} events (M >= 4.5, past 24h)")
                return events
                
        except Exception as e:
            logger.error(f" USGS Earthquake API Error: {str(e)}")
            # return cls._get_mock_data()
            return []
    
    @classmethod
    def _parse_event(cls, feature: Dict) -> Dict[str, Any] | None:
        """Parse USGS GeoJSON feature to internal format"""
        try:
            properties = feature.get("properties", {})
            geometry = feature.get("geometry", {})
            coordinates = geometry.get("coordinates", [0, 0, 0])  # [lon, lat, depth]
            
            magnitude = float(properties.get("mag", 0))
            
            # Determine severity based on magnitude
            if magnitude >= 7.0:
                severity = "critical"
            elif magnitude >= 5.0:
                severity = "high"
            elif magnitude >= 4.0:
                severity = "medium"
            else:
                severity = "low"
            
            # Extract location name
            location_name = properties.get("place", "Unknown Location")
            
            # Extract timestamp (USGS provides milliseconds since epoch)
            event_timestamp = datetime.fromtimestamp(properties.get("time", 0) / 1000)
            
            return {
                "event_type": "earthquake",
                "severity": severity,
                "status": "detected",
                "latitude": float(coordinates[1]) if len(coordinates) > 1 else 0,
                "longitude": float(coordinates[0]) if len(coordinates) > 0 else 0,
                "location_name": location_name,
                "source": "USGS_EARTHQUAKES",
                "event_timestamp": event_timestamp,
                "confidence": 0.98,  # USGS data is highly reliable
                "is_verified": True,
                "data": {
                    "usgs_id": properties.get("id"),
                    "magnitude": magnitude,
                    "depth_km": float(coordinates[2]) if len(coordinates) > 2 else 0,
                    "tsunami": properties.get("tsunami", False),
                    "alert_level": properties.get("alert", "none"),
                    "url": properties.get("url", ""),
                    "felt_reports": properties.get("felt"),
                    "type": properties.get("type", "earthquake"),
                }
            }
        except Exception as e:
            logger.error(f"Error parsing USGS event: {str(e)}")
            return None
