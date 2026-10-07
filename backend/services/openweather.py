"""
OpenWeatherMap API Service
Fetches global weather alerts, storms, and extreme weather conditions
Replaces NOAA for global coverage (not just US)
"""
import httpx
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import os

logger = logging.getLogger(__name__)

class OpenWeatherService:
    """Service to fetch global weather alerts from OpenWeatherMap API"""
    
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    # Cities to monitor globally - covers key disaster-prone regions
    MONITORED_CITIES = [
        # India
        (28.6139, 77.2090, "Delhi", "IN"),
        (19.0760, 72.8777, "Mumbai", "IN"),
        (13.0827, 80.2707, "Chennai", "IN"),
        (23.1815, 79.9864, "Bhopal", "IN"),
        (21.1632, 72.8311, "Surat", "IN"),
        (23.1815, 79.9864, "Indore", "IN"),
        (25.3176, 82.9739, "Varanasi", "IN"),
        (26.2389, 73.0243, "Jodhpur", "IN"),
        (31.7683, 74.8670, "Amritsar", "IN"),
        (26.9124, 75.7873, "Jaipur", "IN"),
        
        # Nepal
        (27.7172, 85.3240, "Kathmandu", "NP"),
        (26.4124, 87.2772, "Janakpur", "NP"),
        (27.8242, 85.9188, "Bhaktapur", "NP"),
        
        # China
        (39.9042, 116.4074, "Beijing", "CN"),
        (31.2304, 121.4737, "Shanghai", "CN"),
        (30.5728, 114.3055, "Wuhan", "CN"),
        (28.2282, 112.9388, "Changsha", "CN"),
        (29.5630, 106.5516, "Chongqing", "CN"),
        (34.3416, 108.9398, "Xi'an", "CN"),
        (23.1291, 113.2644, "Guangzhou", "CN"),
        (22.3193, 114.1694, "Hong Kong", "HK"),
        
        # Bangladesh
        (23.8103, 90.4125, "Dhaka", "BD"),
        (22.3569, 91.7832, "Chittagong", "BD"),
        (24.3745, 88.6041, "Khulna", "BD"),
        
        # Pakistan
        (33.6844, 74.3167, "Islamabad", "PK"),
        (31.5497, 74.3436, "Lahore", "PK"),
        (24.8607, 67.0011, "Karachi", "PK"),
        
        # Southeast Asia
        (13.7563, 100.5018, "Bangkok", "TH"),
        (10.7769, 106.7009, "Ho Chi Minh City", "VN"),
        (21.0285, 105.8542, "Hanoi", "VN"),
        (1.3521, 103.8198, "Singapore", "SG"),
        (3.1390, 101.6869, "Kuala Lumpur", "MY"),
        
        # Middle East
        (33.3128, 44.3615, "Baghdad", "IQ"),
        (24.4539, 54.3773, "Abu Dhabi", "AE"),
        
        # Africa
        (9.0320, 38.7469, "Addis Ababa", "ET"),
        (1.2921, 36.8219, "Nairobi", "KE"),
        (-1.9536, 29.8739, "Kigali", "RW"),
        
        # USA
        (40.7128, -74.0060, "New York", "US"),
        (34.0522, -118.2437, "Los Angeles", "US"),
        (29.7604, -95.3698, "Houston", "US"),
    ]
    
    @classmethod
    async def fetch_events(cls, use_mock: bool = False) -> List[Dict[str, Any]]:
        """
        Fetch global weather alerts from OpenWeatherMap
        
        Args:
            use_mock: If True, return mock data instead of calling API
            
        Returns:
            List of weather event dictionaries
        """
        # 12-Factor App: Strict Environment-Driven Mock Guard
        if use_mock:
            logger.info(" OpenWeather: 🧪 MOCK MODE ENABLED via .env")
            try:
                import json
                from pathlib import Path
                mock_path = Path(__file__).parent.parent / "data" / "mocks" / "openweather.json"
                with open(mock_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load OpenWeather mock: {e}")
                return []
        
        # Strict Live Mode: No mock fallback parameter
        api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        
        if not api_key:
            logger.warning("OPENWEATHERMAP_API_KEY not set in .env. Skipping OpenWeatherMap ingestion.")
            return []
        
        try:
            events = []
            api_key = os.getenv("OPENWEATHERMAP_API_KEY")
            
            # Fetch weather for each city
            for lat, lon, city, country in cls.MONITORED_CITIES:
                try:
                    event = await cls._fetch_city_weather(lat, lon, city, country, api_key)
                    if event:
                        events.append(event)
                except Exception as e:
                    logger.debug(f"Error fetching weather for {city}, {country}: {str(e)}")
                    continue
            
            logger.info(f"OpenWeatherMap: Fetched weather data for {len(events)} cities")
            return events
            
        except Exception as e:
            logger.error(f"OpenWeatherMap API Error: {str(e)}")
            return []
    
    @classmethod
    async def _fetch_city_weather(cls, lat: float, lon: float, city: str, country: str, api_key: str) -> Dict[str, Any] | None:
        """Fetch weather data for a single city"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{cls.BASE_URL}/weather",
                    params={
                        "lat": lat,
                        "lon": lon,
                        "appid": api_key,
                        "units": "metric"  # Celsius
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                # Only create events if there's severe weather
                event = cls._parse_weather(data, city, country)
                return event
                
        except Exception as e:
            logger.debug(f"Error fetching weather for {city}: {str(e)}")
            return None
    
    @classmethod
    def _parse_weather(cls, weather_data: Dict, city: str, country: str) -> Dict[str, Any] | None:
        """Parse OpenWeatherMap weather data to internal event format"""
        try:
            main = weather_data.get("main", {})
            wind = weather_data.get("wind", {})
            clouds = weather_data.get("clouds", {})
            weather = weather_data.get("weather", [{}])[0]
            coord = weather_data.get("coord", {})
            
            temp = main.get("temp", 0)
            humidity = main.get("humidity", 0)
            wind_speed = wind.get("speed", 0)  # m/s
            wind_gust = wind.get("gust", 0)    # m/s
            cloud_cover = clouds.get("all", 0)  # percentage
            
            # Only create event if there's severe weather
            event_type = weather.get("main", "").lower()
            description = weather.get("description", "").lower()
            
            # Filter for severe weather only
            severe_conditions = [
                "thunderstorm", "tornado", "tornado warning",
                "extreme", "severe",
                "heavy rain", "heavy snow",
                "cold", "heat wave",
                "hurricane", "typhoon", "cyclone",
                "hail", "squall", "dust",
                "warning"
            ]
            
            is_severe = any(cond in description for cond in severe_conditions) or \
                       event_type in ["thunderstorm", "tornado", "extreme"] or \
                       wind_speed > 15 or \
                       temp < -10 or temp > 45  # Extreme temps
            
            # Also report if conditions are unusual for the region
            if not is_severe:
                # Check for unusual weather patterns
                if wind_speed > 10 or humidity > 85 or (cloud_cover > 80 and wind_speed > 5):
                    is_severe = True
            
            if not is_severe:
                return None  # Don't create event for normal weather
            
            # Determine severity
            severity = cls._determine_severity(
                event_type, wind_speed, temp, humidity, description
            )
            
            # Determine event type
            event_type_mapped = cls._map_weather_type(event_type, description)
            
            return {
                "event_type": event_type_mapped,
                "severity": severity,
                "status": "detected",
                "latitude": float(coord.get("lat", 0)),
                "longitude": float(coord.get("lon", 0)),
                "location_name": f"{city}, {country}",
                "source": "OPENWEATHER",
                "event_timestamp": datetime.utcnow(),
                "confidence": 0.85,  # Weather forecasts are less certain than earthquakes
                "is_verified": True,
                "data": {
                    "openweather_id": weather.get("id"),
                    "weather_type": event_type,
                    "description": description,
                    "temperature_c": temp,
                    "humidity_percent": humidity,
                    "wind_speed_ms": wind_speed,
                    "wind_gust_ms": wind_gust,
                    "cloud_cover_percent": cloud_cover,
                    "pressure_hpa": main.get("pressure"),
                    "visibility_m": weather_data.get("visibility"),
                    "rain_mm": weather_data.get("rain", {}).get("1h", 0),
                    "snow_mm": weather_data.get("snow", {}).get("1h", 0),
                }
            }
            
        except Exception as e:
            logger.debug(f"Error parsing OpenWeatherMap data for {city}: {str(e)}")
            return None
    
    @classmethod
    def _determine_severity(cls, event_type: str, wind_speed: float, 
                           temp: float, humidity: float, description: str) -> str:
        """Determine severity based on weather parameters"""
        if any(x in event_type for x in ["thunderstorm", "tornado", "extreme", "hurricane", "cyclone"]):
            return "critical"
        if wind_speed > 20: 
            return "critical"
        elif wind_speed > 15: 
            return "high"
        elif wind_speed > 10: 
            return "medium"
        if temp < -15 or temp > 45:
            return "critical"
        elif temp < -5 or temp > 40:
            return "high"
        elif temp < 0 or temp > 35:
            return "medium"
        if "heavy" in description or "extreme" in description:
            return "high"
        if humidity > 85 and wind_speed > 8:
            return "medium"
        return "low"
    
    @classmethod
    def _map_weather_type(cls, event_type: str, description: str) -> str:
        """Map OpenWeatherMap weather type to our event types"""
        event_lower = event_type.lower()
        desc_lower = description.lower()
        
        if any(x in event_lower for x in ["thunderstorm", "storm"]):
            return "thunderstorm"
        elif any(x in event_lower for x in ["tornado", "whirlwind"]):
            return "tornado"
        elif any(x in event_lower for x in ["rain", "drizzle"]):
            return "flood"
        elif any(x in event_lower for x in ["snow", "sleet"]):
            return "winter_storm"
        elif any(x in event_lower for x in ["clear", "sunny"]):
            if any(x in desc_lower for x in ["heat", "extreme heat"]):
                return "heat_wave"
            return "other"
        elif any(x in event_lower for x in ["clouds", "overcast"]):
            return "other"
        elif any(x in desc_lower for x in ["dust", "sand"]):
            return "dust_storm"
        elif any(x in desc_lower for x in ["squall", "gust"]):
            return "high_wind"
        elif any(x in desc_lower for x in ["hail"]):
            return "thunderstorm"
        elif any(x in desc_lower for x in ["cold", "frost", "freeze"]):
            return "winter_storm"
        elif any(x in desc_lower for x in ["heat", "warm"]):
            return "heat_wave"
        return "storm"
