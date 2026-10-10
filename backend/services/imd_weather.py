"""
IMD (India Meteorological Department) Weather Service
Fetches weather and meteorological data for India
"""
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class IMDWeatherService:
    """
    Fetches weather and meteorological data from India Meteorological Department (IMD)
    Additional data source for incidents in India
    """

    IMD_API_ENDPOINT = os.getenv("IMD_API_ENDPOINT", "https://api.imd.gov.in/v1/")
    IMD_API_KEY = os.getenv("IMD_API_KEY")
    IMD_API_JWT_TOKEN = os.getenv("IMD_API_JWT_TOKEN")

    @staticmethod
    def is_india_location(latitude: float, longitude: float) -> bool:
        """
        Check if coordinates are within India bounds
        India: approximately 8°N to 35°N latitude, 68°E to 97°E longitude
        """
        return 8 <= latitude <= 35 and 68 <= longitude <= 97

    @classmethod
    def fetch_events(cls, latitude: float = 0, longitude: float = 0, use_mock: bool = False) -> List[Dict[str, Any]]:
        """
        Fetch meteorological events from IMD for India region
        
        Args:
            latitude: Incident latitude
            longitude: Incident longitude
            use_mock: If True, return mock IMD data for testing
            
        Returns:
            List of weather events from IMD, or empty list if not available
        """
        # Check if this location is in India
        if not cls.is_india_location(latitude, longitude):
            logger.debug(f"[IMD] Location ({latitude}, {longitude}) outside India bounds, skipping IMD")
            return []

        logger.info(f"[IMD] Fetching meteorological data for India location ({latitude}, {longitude})")

        # Return mock data if requested
        if use_mock:
            return cls._get_mock_imd_data(latitude, longitude)

        # Check if credentials are configured
        if not cls.IMD_API_KEY or not cls.IMD_API_JWT_TOKEN:
            logger.warning(f"[IMD] API credentials not configured (IMD_API_KEY, IMD_API_JWT_TOKEN missing in .env)")
            logger.info(f"[IMD] To enable IMD integration: Register at https://api.imd.gov.in/public/register.php and add credentials to .env")
            return []

        try:
            return cls._fetch_from_imd_api(latitude, longitude)
        except Exception as e:
            logger.error(f"[IMD] Failed to fetch data: {e}")
            return []

    @classmethod
    def _fetch_from_imd_api(cls, latitude: float, longitude: float) -> List[Dict[str, Any]]:
        """
        Fetch real data from IMD API
        
        Args:
            latitude: Incident latitude
            longitude: Incident longitude
            
        Returns:
            List of weather events from IMD API
        """
        headers = {
            "Authorization": f"Bearer {cls.IMD_API_JWT_TOKEN}",
            "X-API-Key": cls.IMD_API_KEY,
            "Content-Type": "application/json"
        }

        try:
            # Import requests here to avoid hard dependency
            import requests
            
            # IMD forecast endpoint
            url = f"{cls.IMD_API_ENDPOINT}forecast/location"
            params = {
                "lat": latitude,
                "lon": longitude,
                "apikey": cls.IMD_API_KEY
            }

            logger.info(f"[IMD API CALL] Fetching weather for ({latitude}, {longitude})")
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse IMD response and convert to standard format
            events = cls._parse_imd_response(data, latitude, longitude)
            logger.info(f"[IMD] Retrieved {len(events)} weather events")
            
            return events

        except ImportError:
            logger.warning("[IMD] requests library not installed, skipping IMD API call")
            return []
        except Exception as e:
            logger.error(f"[IMD] API call failed: {e}")
            return []

    @staticmethod
    def _parse_imd_response(response: Dict[str, Any], latitude: float, longitude: float) -> List[Dict[str, Any]]:
        """
        Parse IMD API response and convert to standard event format
        
        Args:
            response: Raw IMD API response
            latitude: Incident latitude
            longitude: Incident longitude
            
        Returns:
            List of standardized weather events
        """
        events = []
        
        try:
            # IMD typically returns forecast data with weather conditions
            # Parse based on actual IMD API response structure
            if "data" in response:
                weather_data = response["data"]
                
                # Create event from IMD data
                event = {
                    "id": f"IMD_{latitude}_{longitude}",
                    "source": "IMD",
                    "location_name": response.get("location_name", "India"),
                    "latitude": latitude,
                    "longitude": longitude,
                    "event_type": "weather_forecast",
                    "severity": cls._determine_severity(weather_data),
                    "status": "active",
                    "event_timestamp": response.get("timestamp", None),
                    "confidence": 0.94,  # IMD confidence for India
                    "data": {
                        "temperature": weather_data.get("temp"),
                        "humidity": weather_data.get("humidity"),
                        "wind_speed": weather_data.get("wind_speed"),
                        "precipitation": weather_data.get("precipitation"),
                        "weather_condition": weather_data.get("condition"),
                        "monsoon_status": weather_data.get("monsoon_status"),
                        "raw_imd_data": weather_data
                    }
                }
                events.append(event)
        except Exception as e:
            logger.error(f"[IMD] Failed to parse response: {e}")

        return events

    @staticmethod
    def _determine_severity(weather_data: Dict[str, Any]) -> str:
        """
        Determine severity level based on weather conditions
        
        Args:
            weather_data: Weather data from IMD
            
        Returns:
            Severity level: 'low', 'medium', 'high', 'critical'
        """
        condition = weather_data.get("condition", "").lower()
        wind_speed = weather_data.get("wind_speed", 0)
        precipitation = weather_data.get("precipitation", 0)

        # Monsoon-related or severe conditions
        if "heavy" in condition or "cyclone" in condition or "extreme" in condition:
            return "critical"
        elif wind_speed > 60 or precipitation > 100:
            return "high"
        elif wind_speed > 40 or precipitation > 50:
            return "medium"
        else:
            return "low"

    @staticmethod
    def _get_mock_imd_data(latitude: float, longitude: float) -> List[Dict[str, Any]]:
        """
        Return mock IMD data for testing/demonstration
        
        Args:
            latitude: Incident latitude
            longitude: Incident longitude
            
        Returns:
            List of mock weather events
        """
        return [
            {
                "id": f"IMD_MOCK_{latitude}_{longitude}",
                "source": "IMD",
                "location_name": "India Meteorological Department Alert",
                "latitude": latitude,
                "longitude": longitude,
                "event_type": "weather_forecast",
                "severity": "high",
                "status": "active",
                "event_timestamp": "2026-10-08T12:00:00Z",
                "confidence": 0.94,
                "data": {
                    "temperature": 28,
                    "humidity": 75,
                    "wind_speed": 45,
                    "precipitation": 85,
                    "weather_condition": "Heavy monsoon rainfall expected",
                    "monsoon_status": "Southwest monsoon active",
                    "alert": "Water crest expected at 4 PM ±30 minutes",
                    "raw_imd_data": {
                        "forecast_period": "0-12 hours",
                        "monsoon_intensity": "strong",
                        "risk_areas": ["Chintamani", "Kolar"],
                        "recommended_action": "Alert flood control authorities"
                    }
                }
            }
        ]
