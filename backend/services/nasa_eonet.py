"""
NASA EONET (Earth Observation Natural Event Tracking) API Service
Fetches real-time natural disaster events from NASA
"""
import httpx
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import os

logger = logging.getLogger(__name__)

class NASAEONETService:
    """Service to fetch disaster events from NASA EONET API"""
    
    BASE_URL = "https://eonet.gsfc.nasa.gov/api/v3"
    
    # Category mappings: NASA categories to our event types (keys lowercased for case-insensitive match)
    CATEGORY_MAPPING = {
        'floods': 'flood',
        'wildfires': 'fire',
        'fires': 'fire',
        'earthquakes': 'earthquake',
        'volcanoes': 'volcano',
        'severestorms': 'storm',
        'storms': 'storm',
        'severe_storms': 'storm',
        'dustaerosol': 'aerosol',
        'dust_aerosol': 'aerosol',
        'landslides': 'landslide',
        'land_slides': 'landslide',
        'snowice': 'snow_ice',
        'snow_ice': 'snow_ice',
        'drought': 'drought',
        'tempextremes': 'temperature_extreme',
        'watercolor': 'water_color',
        'manmade': 'other',
    }
    
    SEVERITY_MAPPING = {
        1: 'low',
        2: 'low',
        3: 'medium',
        4: 'medium',
        5: 'high',
        6: 'high',
        7: 'critical',
        8: 'critical',
    }
    
    @classmethod
    async def fetch_events(cls, use_mock: bool = False) -> List[Dict[str, Any]]:
        """
        Fetch current natural disaster events from NASA EONET v3.1 GeoJSON API
        
        Args:
            use_mock: If True, return mock data instead of calling API
            
        Returns:
            List of event dictionaries
        """
        if use_mock:
            logger.info(" NASA EONET: 🧪 MOCK MODE ENABLED via .env")
            return cls._get_mock_data()
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{cls.BASE_URL}/events/geojson",
                    params={
                        "status": "open",  # Only open/ongoing events
                        "limit": 100
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                events = []
                features = data.get("features", [])
                for feature in features:
                    parsed = cls._parse_event(feature)
                    if parsed:
                        events.append(parsed)
                
                logger.info(f" NASA EONET: Fetched {len(events)} events")
                return events
                
        except Exception as e:
            logger.error(f" NASA EONET API Error: {str(e)}")
            return []
    
    @classmethod
    def _parse_event(cls, feature: Dict) -> Dict[str, Any] | None:
        """Parse NASA EONET v3.1 GeoJSON Feature to internal format"""
        try:
            properties = feature.get("properties", {})
            geometry = feature.get("geometry", {})
            
            # Get event category
            categories = properties.get("categories", [])
            category = categories[0].get("id", "").lower() if categories else ""
            event_type = cls.CATEGORY_MAPPING.get(category, "other")
            
            # Extract coordinates from GeoJSON
            coords = cls._extract_point(geometry.get("coordinates", [0, 0]))
            
            # Use exact physical magnitude for threat scoring if available
            mag_value = properties.get("magnitudeValue")
            mag_unit = properties.get("magnitudeUnit")
            
            # Build event
            return {
                "event_type": event_type,
                "severity": "medium",  # Calculated dynamically later in impact_analysis
                "status": "detected" if not properties.get("closed") else "resolved",
                "latitude": coords[1] if len(coords) > 1 else 0,
                "longitude": coords[0] if len(coords) > 0 else 0,
                "location_name": properties.get("title", "Unknown"),
                "source": "NASA_EONET",
                "event_timestamp": cls._parse_date(properties.get("date")),
                "confidence": 0.95,  # NASA data is highly reliable
                "is_verified": True,
                "data": {
                    "nasa_id": properties.get("id"),
                    "category": category,
                    "description": properties.get("description", ""),
                    "link": properties.get("link", ""),
                    "geometry_type": geometry.get("type"),
                    "magnitude_value": mag_value,
                    "magnitude_unit": mag_unit
                }
            }
        except Exception as e:
            logger.error(f"Error parsing NASA GeoJSON event: {str(e)}")
            return None
    
    @classmethod
    def _extract_point(cls, coordinates: Any) -> List[float]:
        """
        Extract a single [lon, lat] point from a coordinates structure,
        which may be a flat point, or a nested Polygon/LineString/MultiPoint array.
        """
        # Drill down into nested lists until we find a pair of numbers
        current = coordinates
        while isinstance(current, list) and current and isinstance(current[0], list):
            current = current[0]
        if isinstance(current, list) and len(current) >= 2 and all(
            isinstance(v, (int, float)) for v in current[:2]
        ):
            return current
        return [0, 0]
    
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
        """Return mock NASA EONET data for testing"""
        now = datetime.utcnow()
        return [
            {
                "event_type": "fire",
                "severity": "high",
                "status": "detected",
                "latitude": 36.1699,
                "longitude": -119.4179,
                "location_name": "California Wildfires - Sierra Nevada",
                "source": "NASA_EONET",
                "event_timestamp": now - timedelta(hours=2),
                "confidence": 0.95,
                "is_verified": True,
                "data": {
                    "nasa_id": "EONET_MOCK_001",
                    "category": "fires",
                    "description": "Active wildfires detected in California Sierra Nevada region",
                    "link": "https://eonet.gsfc.nasa.gov",
                    "geometry_type": "Point"
                }
            },
            {
                "event_type": "earthquake",
                "severity": "medium",
                "status": "detected",
                "latitude": 34.0522,
                "longitude": -118.2437,
                "location_name": "Los Angeles Seismic Activity",
                "source": "NASA_EONET",
                "event_timestamp": now - timedelta(hours=4),
                "confidence": 0.92,
                "is_verified": True,
                "data": {
                    "nasa_id": "EONET_MOCK_002",
                    "category": "earthquakes",
                    "description": "Seismic activity detected near Los Angeles",
                    "link": "https://eonet.gsfc.nasa.gov",
                    "geometry_type": "Point"
                }
            },
            {
                "event_type": "flood",
                "severity": "high",
                "status": "detected",
                "latitude": 38.5816,
                "longitude": -121.4944,
                "location_name": "Sacramento Valley Flooding",
                "source": "NASA_EONET",
                "event_timestamp": now - timedelta(hours=6),
                "confidence": 0.88,
                "is_verified": True,
                "data": {
                    "nasa_id": "EONET_MOCK_003",
                    "category": "floods",
                    "description": "Flooding detected in Sacramento Valley",
                    "link": "https://eonet.gsfc.nasa.gov",
                    "geometry_type": "Point"
                }
            }
        ]
