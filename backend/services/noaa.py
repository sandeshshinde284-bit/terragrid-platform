"""
NOAA (National Oceanic and Atmospheric Administration) API Service
Fetches severe weather, storms, and hurricane data
"""
import httpx
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import os

logger = logging.getLogger(__name__)

class NOAAService:
    """Service to fetch weather and storm events from NOAA API"""
    
    BASE_URL = "https://api.weather.gov"
    ALERTS_URL = "https://api.weather.gov/alerts/active"
    
    @classmethod
    async def fetch_events(cls, use_mock: bool = False) -> List[Dict[str, Any]]:
        """
        Fetch active severe weather alerts from NOAA
        
        Args:
            use_mock: If True, return mock data instead of calling API
            
        Returns:
            List of weather event dictionaries
        """
        # 12-Factor App: Strict Environment-Driven Mock Guard
        if use_mock:
            logger.info(" NOAA Weather: 🧪 MOCK MODE ENABLED via .env")
            try:
                import json
                from pathlib import Path
                mock_path = Path(__file__).parent.parent / "data" / "mocks" / "noaa.json"
                with open(mock_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load NOAA mock: {e}")
                return []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Fetch active alerts - uses US grid points
                # For California specifically
                response = await client.get(
                    cls.ALERTS_URL,
                    params={
                        "status": "actual"
                    },
                    timeout=30.0,
                    headers={
                        "User-Agent": "(TerraGrid, contact@terragrid.ai)"  # NOAA requires User-Agent
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                events = []
                for feature in data.get("features", []):
                    parsed = cls._parse_event(feature)
                    if parsed:
                        events.append(parsed)
                
                logger.info(f" NOAA Weather: Fetched {len(events)} events")
                return events
                
        except Exception as e:
            logger.error(f" NOAA API Error: {str(e)}")
            # return cls._get_mock_data()
            return []
    
    @classmethod
    def _parse_event(cls, feature: Dict) -> Dict[str, Any] | None:
        """Parse NOAA GeoJSON feature to internal format"""
        try:
            properties = feature.get("properties", {})
            geometry = feature.get("geometry", {})
            
            # Extract event type from alert
            alert_type = properties.get("event", "Weather Alert").lower()
            
            # Map NOAA alert types to our event types
            event_type = cls._map_alert_type(alert_type)
            
            # Determine severity
            severity_map = {
                "extreme": "critical",
                "severe": "high",
                "moderate": "medium",
                "minor": "low",
                "unknown": "medium",
            }
            severity = severity_map.get(
                properties.get("severity", "unknown").lower(),
                "medium"
            )
            
            # Get coordinates (centroid of affected area)
            coords = cls._extract_centroid(geometry)
            
            # Extract area name
            area = properties.get("areaDesc", "Unknown Area")
            # Add country code for NOAA (US weather service)
            location_name = f"{area}, US"
            effective = properties.get("effective")
            expires = properties.get("expires")
            
            if effective:
                event_timestamp = cls._parse_date(effective)
            else:
                event_timestamp = datetime.utcnow()
            
            return {
                "event_type": event_type,
                "severity": severity,
                "status": "detected",
                "latitude": coords[1],
                "longitude": coords[0],
                "location_name": location_name,
                "source": "NOAA_WEATHER",
                "event_timestamp": event_timestamp,
                "confidence": 0.92,  # NOAA is reliable but less precise than seismic
                "is_verified": True,
                "data": {
                    "noaa_id": properties.get("id"),
                    "event": alert_type,
                    "headline": properties.get("headline", ""),
                    "description": properties.get("description", ""),
                    "instruction": properties.get("instruction", ""),
                    "urgency": properties.get("urgency", ""),
                    "severity": properties.get("severity", ""),
                    "certainty": properties.get("certainty", ""),
                    "effective": effective,
                    "expires": expires,
                    "status": properties.get("status", ""),
                    "sender_name": properties.get("senderName", ""),
                }
            }
        except Exception as e:
            logger.error(f"Error parsing NOAA event: {str(e)}")
            return None
    
    @classmethod
    def _map_alert_type(cls, alert_type: str) -> str:
        """Map NOAA alert type to our event types"""
        alert_lower = alert_type.lower()
        
        if any(x in alert_lower for x in ['hurricane', 'typhoon', 'cyclone']):
            return "hurricane"
        elif any(x in alert_lower for x in ['tornado', 'waterspout']):
            return "tornado"
        elif any(x in alert_lower for x in ['flood', 'flash flood']):
            return "flood"
        elif any(x in alert_lower for x in ['winter', 'snow', 'ice', 'blizzard']):
            return "winter_storm"
        elif any(x in alert_lower for x in ['heat', 'extreme heat']):
            return "heat_wave"
        elif any(x in alert_lower for x in ['thunderstorm', 'severe storm']):
            return "thunderstorm"
        elif any(x in alert_lower for x in ['wind', 'high wind']):
            return "high_wind"
        elif any(x in alert_lower for x in ['dust', 'dust storm']):
            return "dust_storm"
        else:
            return "storm"
    
    @classmethod
    def _extract_centroid(cls, geometry: Dict) -> tuple:
        """
        Extract centroid from GeoJSON geometry
        Handles: Point, Polygon, MultiPolygon, etc.
        Returns: [lon, lat] or [0, 0] if unable to extract
        """
        try:
            geom_type = geometry.get("type", "").lower()
            coords = geometry.get("coordinates", [])
            
            if geom_type == "point" and coords:
                return [float(coords[0]), float(coords[1])]
            
            elif geom_type == "polygon" and coords:
                # Get centroid of polygon
                return cls._polygon_centroid(coords[0])
            
            elif geom_type == "multipolygon" and coords:
                # Use first polygon
                if coords[0]:
                    return cls._polygon_centroid(coords[0][0])
            
            return [0, 0]
        except:
            return [0, 0]
    
    @classmethod
    def _polygon_centroid(cls, ring: List[List[float]]) -> tuple:
        """Calculate centroid of polygon ring"""
        if not ring or len(ring) < 3:
            return [0, 0]
        
        # Simple centroid calculation
        lons = [p[0] for p in ring]
        lats = [p[1] for p in ring]
        
        return [
            sum(lons) / len(lons),
            sum(lats) / len(lats)
        ]
    
    @classmethod
    def _parse_date(cls, date_str: str | None) -> datetime:
        """Parse ISO date string"""
        if not date_str:
            return datetime.utcnow()
        try:
            # NOAA uses ISO 8601 format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return datetime.utcnow()
