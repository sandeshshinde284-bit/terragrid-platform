from backend.config import settings
"""
OpenWeatherMap API Service
Fetches global weather alerts, storms, and extreme weather conditions
Replaces NOAA for global coverage (not just US)
"""
import asyncio
import httpx
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import os
from backend.utils.data_logger import log_raw_data

logger = logging.getLogger(__name__)

class OpenWeatherService:
    """Service to fetch global weather alerts from OpenWeatherMap API"""

    BASE_URL = settings.OPENWEATHER_API_URL

    
    # one at a time, each opening its own httpx.AsyncClient (fresh TLS handshake
    # per city). That serialized ~40 round-trips end-to-end, which is what made
    # every PREPARE-phase page (Forecast, Risk Timeline, Checklist, Agency
    # Alerts - each of which independently calls this method on mount) take
    # 3-5 minutes to load. Fixed by fetching all cities concurrently off one
    # shared client, plus a short in-memory cache so the four pages don't each
    # pay for a fresh 40-city fetch when navigated between in quick succession.
    _FORECAST_FETCH_CONCURRENCY = 10
    _forecast_cache: List[Dict[str, Any]] | None = None
    _forecast_cache_at: float = 0.0
    FORECAST_CACHE_TTL_SECONDS = 600  # 10 minutes

    
    # entries; below half of that, a day's risk_level/confidence_pct call is
    # real but thin evidence (see _summarize_forecast_by_day).
    MIN_SUFFICIENT_ENTRIES = 4

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
            logger.info("OpenWeather: mock mode enabled (MOCK_MODE=true in .env), skipping live API call")
            try:
                import json
                from pathlib import Path
                mock_path = Path(__file__).parent.parent / "data" / "mocks" / "openweather.json"
                with open(mock_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load OpenWeather mock: {e}")
                return []
        
        
        api_key = settings.OPENWEATHERMAP_API_KEY
        
        if not api_key:
            logger.warning("[FEATURE_HEALTH] feature=openweather_current status=no_api_key reason=OPENWEATHERMAP_API_KEY not set in .env")
            return []

        try:
            events = []
            api_key = settings.OPENWEATHERMAP_API_KEY

            # Fetch weather for each city
            for lat, lon, city, country in cls.MONITORED_CITIES:
                try:
                    event = await cls._fetch_city_weather(lat, lon, city, country, api_key)
                    if event:
                        events.append(event)
                except Exception as e:
                    logger.debug(f"Error fetching weather for {city}, {country}: {str(e)}")
                    continue

            logger.info(f"[FEATURE_HEALTH] feature=openweather_current status=success cities_queried={len(cls.MONITORED_CITIES)} severe_events_found={len(events)}")
            return events

        except Exception as e:
            logger.error(f"[FEATURE_HEALTH] feature=openweather_current status=error error={type(e).__name__}: {e}")
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
    async def fetch_forecast(cls, use_mock: bool = False) -> List[Dict[str, Any]]:
        """
        Fetch 5-day/3-hour-step forecasts for all monitored cities and collapse
        each city's forecast into a day-by-day risk escalation timeline.

        Uses the same free-tier OpenWeatherMap endpoint family as fetch_events()
        (/data/2.5/forecast instead of /data/2.5/weather), the same API key, and
        the same severity/type-mapping logic, so forecast risk and current-weather
        risk can never drift out of sync with each other.

        Args:
            use_mock: If True, return mock data instead of calling API

        Returns:
            List of per-city forecast dicts, each with a "daily" list of
            {date, risk_level, dominant_weather, max_wind_ms, min_temp_c, max_temp_c,
             total_rain_mm, confidence_pct, alert_recommended, entries_count,
             supporting_entries, data_sufficient, severity_reason, raw_entries}
        """
        if use_mock:
            logger.info("OpenWeather forecast: mock mode enabled (MOCK_MODE=true in .env), skipping live API call")
            try:
                import json
                from pathlib import Path
                mock_path = Path(__file__).parent.parent / "data" / "mocks" / "openweather_forecast.json"
                with open(mock_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load OpenWeather forecast mock: {e}")
                return []

        api_key = settings.OPENWEATHERMAP_API_KEY

        if not api_key:
            logger.warning("[FEATURE_HEALTH] feature=openweather_forecast status=no_api_key reason=OPENWEATHERMAP_API_KEY not set in .env")
            return []

        # Serve from the short-lived in-memory cache when fresh. All four
        # PREPARE-phase pages (Forecast, Risk Timeline, Checklist, Agency
        # Alerts) call this independently on mount - without this, navigating
        # between them re-pays the full 40-city fetch every single time.
        now = time.monotonic()
        if cls._forecast_cache is not None and (now - cls._forecast_cache_at) < cls.FORECAST_CACHE_TTL_SECONDS:
            age = now - cls._forecast_cache_at
            logger.info(f"OpenWeatherMap: Serving cached 5-day forecast ({len(cls._forecast_cache)} cities, age={age:.0f}s)")
            return cls._forecast_cache

        semaphore = asyncio.Semaphore(cls._FORECAST_FETCH_CONCURRENCY)

        async def fetch_one(client: httpx.AsyncClient, lat: float, lon: float, city: str, country: str):
            async with semaphore:
                try:
                    return await cls._fetch_city_forecast(client, lat, lon, city, country, api_key)
                except Exception as e:
                    logger.debug(f"Error fetching forecast for {city}, {country}: {str(e)}")
                    return None

        # One shared client (connection pooling) instead of a new client per
        # city, fetched concurrently (bounded by the semaphore above) instead
        # of one-at-a-time - this is what cuts ~40 sequential round-trips
        # down to a handful of concurrent batches.
        async with httpx.AsyncClient(timeout=20.0) as client:
            results = await asyncio.gather(*[
                fetch_one(client, lat, lon, city, country)
                for lat, lon, city, country in cls.MONITORED_CITIES
            ])

        forecasts = [f for f in results if f]

        cls._forecast_cache = forecasts
        cls._forecast_cache_at = now

        log_raw_data("openweather_forecast", forecasts)
        logger.info(f"[FEATURE_HEALTH] feature=openweather_forecast status=success cities_fetched={len(forecasts)} cities_queried={len(cls.MONITORED_CITIES)} concurrency={cls._FORECAST_FETCH_CONCURRENCY}")
        return forecasts

    @classmethod
    def get_forecast_cache_age_seconds(cls) -> float | None:
        """
        Phase (source-of-truth validation): how old is the forecast data
        fetch_forecast() is currently serving from cache, in seconds.
        None means no live fetch has ever populated the cache yet (e.g.
        only mock mode has run, or the server just started).
        """
        if cls._forecast_cache is None:
            return None
        return round(time.monotonic() - cls._forecast_cache_at, 1)

    @classmethod
    async def _fetch_city_forecast(cls, client: httpx.AsyncClient, lat: float, lon: float, city: str, country: str, api_key: str) -> Dict[str, Any] | None:
        """Fetch and summarize the 5-day/3-hour-step forecast for a single city, using a shared client."""
        try:
            response = await client.get(
                f"{cls.BASE_URL}/forecast",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": api_key,
                    "units": "metric",
                }
            )
            response.raise_for_status()
            data = response.json()

            daily = cls._summarize_forecast_by_day(data.get("list", []))
            if not daily:
                return None

            return {
                "city": city,
                "country": country,
                "latitude": lat,
                "longitude": lon,
                "source": "OPENWEATHER",
                "daily": daily,
            }

        except Exception as e:
            logger.debug(f"Error fetching forecast for {city}: {str(e)}")
            return None

    @classmethod
    def _summarize_forecast_by_day(cls, entries: List[Dict]) -> List[Dict[str, Any]]:
        """
        Collapse OpenWeatherMap's 3-hour-step forecast list (~40 entries over 5 days)
        into one risk-escalation entry per calendar day, reusing the same severity
        thresholds as the current-weather path.
        """
        from collections import defaultdict

        by_day: Dict[str, List[Dict]] = defaultdict(list)
        for entry in entries:
            dt_txt = entry.get("dt_txt", "")
            day_key = dt_txt.split(" ")[0] if dt_txt else None
            if not day_key:
                continue
            by_day[day_key].append(entry)

        daily_summaries = []
        for day_key in sorted(by_day.keys()):
            day_entries = by_day[day_key]

            max_wind = 0.0
            min_temp = float("inf")
            max_temp = float("-inf")
            total_rain = 0.0
            worst_severity = None
            dominant_weather = None
            worst_reason = None
            best_rain_for_tiebreak = -1.0
            severity_rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}

            # independent 3-hour forecasts. If only one of those 8 reaches
            # the day's worst severity and the rest are calm, that's a brief
            # spike, not a sustained risk - alerting on it as confidently as
            # a day where all 8 agree would be a false alarm. entry_severities
            # collects every entry's own severity so we can measure, after
            # the loop, what fraction of the day actually agrees with
            # worst_severity - a real, computed-from-data signal, not an
            # invented probability (OpenWeatherMap's free forecast tier has
            # no confidence field of its own to use instead).
            entry_severities: List[str] = []

            # The actual 3-hour readings behind this day's call, kept so the
            # UI can show real "audit evidence" (what OpenWeatherMap actually
            # returned, with its own timestamp) instead of just the derived
            # risk_level - without this there was no way to trace a day's
            # call back to the raw forecast data it came from.
            raw_entries: List[Dict[str, Any]] = []

            for entry in day_entries:
                main = entry.get("main", {})
                wind = entry.get("wind", {})
                weather = entry.get("weather", [{}])[0]

                temp = main.get("temp", 0)
                humidity = main.get("humidity", 0)
                wind_speed = wind.get("speed", 0)
                rain_mm = entry.get("rain", {}).get("3h", 0)

                min_temp = min(min_temp, temp)
                max_temp = max(max_temp, temp)
                max_wind = max(max_wind, wind_speed)
                total_rain += rain_mm

                event_type = weather.get("main", "").lower()
                description = weather.get("description", "").lower()
                # OpenWeatherMap's own "weather.main" field (Clear, Clouds, Rain,
                # Drizzle, Thunderstorm, Snow, Mist...) is already a clean, accurate
                # label on its own - use it directly for display instead of forcing
                # it through _map_weather_type(), which is built for *incident*
                # categorization and collapses any non-severe condition (including
                # plain "Clear") down to "other".
                weather_label = weather.get("main", "Unknown")

                severity = cls._determine_severity(event_type, wind_speed, temp, humidity, description)
                entry_severities.append(severity)

                raw_entries.append({
                    "time": entry.get("dt_txt", ""),
                    "temp_c": round(temp, 1),
                    "wind_ms": round(wind_speed, 1),
                    "humidity_pct": humidity,
                    "rain_mm": round(rain_mm, 1),
                    "weather": weather_label,
                    "severity": severity,
                })

                # Pick the entry that best represents the day: highest severity first,
                # and among equally-severe entries (including the common all-"low" day),
                # the one with the most rain - so a calm-but-rainy day doesn't get
                # mislabeled "clear" just because nothing crossed a severity threshold.
                # worst_severity starts as None (not "low") so the first entry always
                # sets a real, observed weather type instead of a hardcoded default.
                is_more_severe = worst_severity is None or severity_rank.get(severity, 0) > severity_rank.get(worst_severity, 0)
                is_tie_but_rainier = severity_rank.get(severity, 0) == severity_rank.get(worst_severity, 0) and rain_mm > best_rain_for_tiebreak
                if is_more_severe or is_tie_but_rainier:
                    worst_severity = severity
                    dominant_weather = weather_label
                    worst_reason = cls._severity_reason(event_type, wind_speed, temp, humidity, description)
                    best_rain_for_tiebreak = rain_mm

            worst_severity = worst_severity or "low"
            dominant_weather = dominant_weather or "Clear"  # only if day_entries was somehow empty
            worst_reason = worst_reason or "no threshold was crossed - calm conditions"

            # Map internal severity scale to the UI's YELLOW/ORANGE/RED escalation bands
            risk_level = {
                "low": "GREEN",
                "medium": "YELLOW",
                "high": "ORANGE",
                "critical": "RED",
            }.get(worst_severity, "GREEN")

            
            # 3-hour entries actually reached the severity we picked as the
            # day's worst? A day where 7 of 8 entries are "high" is a
            # sustained risk; a day where only 1 of 8 spikes to "high" and
            # the rest are "low" is a brief, isolated reading - both would
            # otherwise render as the same ORANGE node. This is computed
            # directly from the entries already fetched above, not an
            # invented number.
            worst_rank = severity_rank.get(worst_severity, 0)
            supporting_count = sum(
                1 for s in entry_severities if severity_rank.get(s, 0) >= worst_rank
            )
            total_count = len(entry_severities)
            confidence_pct = (
                round(100 * supporting_count / total_count, 1) if total_count else 0.0
            )
            # Only worth an operator's attention if the forecast both says
            # something is wrong (non-GREEN) and most of the day's entries
            # agree on it - a lone noisy 3-hour spike shouldn't trigger the
            # same alert recommendation as a sustained, well-supported one.
            alert_recommended = risk_level != "GREEN" and confidence_pct >= 70

            
            # is 8 three-hour entries, but OpenWeatherMap's 5-day window
            # starts from "now" (not midnight) and ends mid-day 5 - so the
            # first and last calendar day in the window are naturally built
            # from fewer entries than the middle days. confidence_pct above
            # is still computed honestly either way, but "100% agreement"
            # from 8 entries and "100% agreement" from 2 entries aren't the
            # same strength of evidence, and nothing before this surfaced
            # the difference. data_sufficient flags a day as backed by at
            # least half a full day's readings (4 of 8) - below that, the
            # call is real but thin, and callers should say so.
            data_sufficient = total_count >= cls.MIN_SUFFICIENT_ENTRIES

            daily_summaries.append({
                "date": day_key,
                "risk_level": risk_level,
                "dominant_weather": dominant_weather,
                "max_wind_ms": round(max_wind, 1),
                "min_temp_c": round(min_temp, 1) if min_temp != float("inf") else None,
                "max_temp_c": round(max_temp, 1) if max_temp != float("-inf") else None,
                "total_rain_mm": round(total_rain, 1),
                "confidence_pct": confidence_pct,
                "alert_recommended": alert_recommended,
                "entries_count": total_count,
                # The actual numerator behind confidence_pct (entries_count is the
                # denominator) - sent as its own real number rather than making
                # the frontend reverse-engineer it from a rounded percentage, so
                # "X of Y checkpoints agreed" is always exact, not an approximation.
                "supporting_entries": supporting_count,
                "data_sufficient": data_sufficient,
                # Why risk_level is what it is, in the terms _determine_severity
                # actually used (wind/temp/humidity/description thresholds) -
                # not a generic restatement of the risk level itself.
                "severity_reason": worst_reason,
                # The raw 3-hour entries this day's call was computed from -
                # real audit evidence, not a log file nobody can see from the UI.
                "raw_entries": raw_entries,
            })

        return daily_summaries

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
    def _severity_reason(cls, event_type: str, wind_speed: float,
                          temp: float, humidity: float, description: str) -> str:
        """
        Plain-language statement of *which* branch of _determine_severity
        actually fired for one 3-hour entry - mirrors that method's checks
        in the same order, so the text always matches the real rule that
        set the severity, not a generic "weather looks bad" summary. Used
        to answer "why is this risk level what it is" honestly, instead of
        inventing a cause (e.g. "rainfall exceeded a threshold") that isn't
        actually how risk_level gets computed.
        """
        if any(x in event_type for x in ["thunderstorm", "tornado", "extreme", "hurricane", "cyclone"]):
            return f"OpenWeatherMap reported {event_type} conditions"
        if wind_speed > 20:
            return f"wind speed {wind_speed:.0f} m/s is above the 20 m/s critical threshold"
        elif wind_speed > 15:
            return f"wind speed {wind_speed:.0f} m/s is above the 15 m/s high-risk threshold"
        elif wind_speed > 10:
            return f"wind speed {wind_speed:.0f} m/s is above the 10 m/s elevated threshold"
        if temp < -15 or temp > 45:
            return f"temperature {temp:.0f}°C is past the -15/45°C critical range"
        elif temp < -5 or temp > 40:
            return f"temperature {temp:.0f}°C is past the -5/40°C high-risk range"
        elif temp < 0 or temp > 35:
            return f"temperature {temp:.0f}°C is past the 0/35°C elevated range"
        if "heavy" in description or "extreme" in description:
            return f"forecast describes \"{description}\" conditions"
        if humidity > 85 and wind_speed > 8:
            return f"humidity {humidity:.0f}% combined with wind speed {wind_speed:.0f} m/s"
        return "no threshold was crossed - calm conditions"

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
