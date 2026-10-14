from backend.config import settings
"""
Feature 3A: Evacuation Zone Mapping Service
Calculates evacuation zones around disaster incidents
"""
import logging
import math
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import os

logger = logging.getLogger(__name__)


class EvacuationZoneService:
    """Service to calculate evacuation zones from incidents"""
    
    # Zone definitions: (zone_number, min_radius_km, max_radius_km, severity_level, color)
    ZONE_DEFINITIONS = [
        (1, 0, 5, "danger", "#FF0000"),      # Red - Immediate evacuation
        (2, 5, 10, "warning", "#FF9500"),    # Orange - Prepare to evacuate
        (3, 10, 25, "caution", "#FFFF00"),   # Yellow - Monitor situation
        (4, 25, 50, "alert", "#ADD8E6"),     # Light Blue - Be aware
    ]
    
    # Zone radius multipliers based on incident severity
    SEVERITY_MULTIPLIERS = {
        "low": 0.5,
        "medium": 1.0,
        "high": 1.5,
        "critical": 2.0,
    }
    
    # Population density by area type (people/km²). Anchored to real published
    # reference figures rather than round guesses - megacity cores worldwide
    # (Mumbai, Dhaka, Manila) run 20,000-40,000/km², a typical large-city
    # built-up area runs 5,000-10,000/km², a mid-size urban area 2,000-4,000,
    # a suburb or small town a few hundred, and rural/wilderness areas are
    # usually under 50/km² (world average land population density is ~50-60/
    # km² including cities - true rural land is far below that). The old
    # values here (500 "rural", 100 "very_rural") were an order of magnitude
    # too high for anywhere that isn't a small town, which is what let a
    # single incident's zone math produce tens of millions of "affected"
    # people for a sparsely populated area - see _determine_area_type below
    # for the area-classification half of that same bug.
    POPULATION_DENSITY = {
        "dense_urban": 15000,
        "urban": 5000,
        "suburban": 1500,
        "rural": 100,
        "very_rural": 15,
    }

    # Radius cap (post-severity-multiplier), km. ZONE_DEFINITIONS' outer band
    # tops out at 50km, and SEVERITY_MULTIPLIERS can double that for a
    # "critical" incident - an uncapped 100km-radius alert zone is not an
    # operationally real evacuation/alert boundary for a single incident, and
    # squares the area (and therefore the population estimate) for every km
    # past what's realistic. Capping here, rather than just lowering the
    # multiplier, keeps the multiplier's intent (critical incidents get a
    # bigger zone than low-severity ones) while stopping the math from
    # compounding into an absurd total for the most severe incidents.
    MAX_ZONE_RADIUS_KM = 40.0

    # Exposure weight per zone, applied on top of POPULATION_DENSITY. Zones 1
    # ("danger", immediate evacuation) and 2 ("warning", prepare to evacuate)
    # are counted at full local density - that's genuinely who's in the
    # hazard's direct path. Zones 3 ("caution", monitor) and 4 ("alert", be
    # aware) are much larger advisory bands; treating their entire ring as
    # uniformly built up at the same density as the core - especially near a
    # megacity - is what let one incident near Delhi produce a population
    # estimate bigger than Delhi NCR's actual population. Weighting them down
    # reflects that an advisory 25-40km out covers a lot of area that isn't
    # uniformly dense, without pretending TerraGrid has a real population
    # raster to compute it exactly.
    ZONE_EXPOSURE_WEIGHT = {1: 1.0, 2: 1.0, 3: 0.3, 4: 0.1}

    OSRM_URL = settings.OSRM_API_URL
    
    @classmethod
    def calculate_zones(cls, incident: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate evacuation zones around an incident
        
        Args:
            incident: {
                latitude, longitude, severity, event_type,
                location_name, threat_score, population_at_risk (optional)
            }
        
        Returns:
            zones_data: {
                incident_id, incident_center, zones: [...],
                evacuation_times, population_affected
            }
        """
        try:
            lat = float(incident.get("latitude", 0))
            lon = float(incident.get("longitude", 0))
            severity = incident.get("severity", "medium").lower()
            event_type = incident.get("event_type", "other")
            threat_score = incident.get("threat_score", incident.get("impact", {}).get("threat_score", 50))
            location_name = incident.get("location_name", "Unknown Location")
            
            # Get severity multiplier
            multiplier = cls.SEVERITY_MULTIPLIERS.get(severity, 1.0)
            
            # Determine area type (simplified - could use actual GIS data)
            area_type = cls._determine_area_type(lat, lon)
            
            # Calculate zones
            zones = []
            total_population = 0
            
            for zone_num, min_radius, max_radius, zone_severity, color in cls.ZONE_DEFINITIONS:
                # Apply severity multiplier, then cap at MAX_ZONE_RADIUS_KM -
                # see that constant's comment for why an uncapped multiplier
                # produces unrealistic zone sizes (and population totals) for
                # critical-severity incidents.
                actual_min = min(min_radius * multiplier, cls.MAX_ZONE_RADIUS_KM)
                actual_max = min(max_radius * multiplier, cls.MAX_ZONE_RADIUS_KM)

                # Calculate zone area in km²
                # Area of ring = π(R² - r²)
                area_km2 = math.pi * (actual_max**2 - actual_min**2)
                
                # Estimate population in this zone - see ZONE_EXPOSURE_WEIGHT
                # for why zones 3/4 count at a fraction of full density.
                density = cls.POPULATION_DENSITY.get(area_type, 200)
                exposure_weight = cls.ZONE_EXPOSURE_WEIGHT.get(zone_num, 1.0)
                population = int(area_km2 * density * exposure_weight)
                total_population += population
                
                # Generate circle coordinates (GeoJSON polygon)
                coordinates = cls._generate_circle_coordinates(lat, lon, actual_max)
                
                zone_data = {
                    "zone_id": zone_num,
                    "zone_number": zone_num,
                    "severity": zone_severity,
                    "color": color,
                    "radius_min_km": round(actual_min, 1),
                    "radius_max_km": round(actual_max, 1),
                    "area_km2": round(area_km2, 1),
                    "population_estimate": population,
                    "coordinates": coordinates,  # GeoJSON polygon
                    "properties": {
                        "name": f"Zone {zone_num} - {zone_severity.upper()}",
                        "severity": zone_severity,
                        "population": population,
                        "area_km2": round(area_km2, 1),
                    }
                }
                zones.append(zone_data)
                
                logger.debug(f"Zone {zone_num}: {population} people in {round(area_km2, 1)} km²")
            
            # Calculate evacuation times (hours)
            evacuation_times = cls._calculate_evacuation_times(zones, event_type)
            
            # Generate incident ID
            incident_id = incident.get("data", {}).get("nasa_id") or \
                         incident.get("data", {}).get("usgs_id") or \
                         f"{location_name}_{threat_score}"
            
            result = {
                "incident_id": incident_id,
                "incident_center": {
                    "latitude": lat,
                    "longitude": lon,
                    "location_name": location_name,
                },
                "incident_severity": severity,
                "event_type": event_type,
                "threat_score": threat_score,
                "zones": zones,
                "total_population_affected": total_population,
                "evacuation_times_hours": evacuation_times,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            logger.info(f"[FEATURE_HEALTH] feature=evacuation_zones status=success location={location_name} affected_population={total_population}")
            return result
            
        except Exception as e:
            logger.error(f"[FEATURE_HEALTH] feature=evacuation_zones status=error error={type(e).__name__}: {e}")
            return {"error": str(e), "zones": []}
    
    # Density tier for every city TerraGrid actually monitors (see
    # OpenWeatherService.MONITORED_CITIES - same list, reused here rather
    # than duplicated, so adding a monitored city automatically gives it a
    # real density anchor instead of silently falling through to "rural").
    # Tiers are a general-knowledge call per city (a few are genuinely
    # borderline, e.g. Jaipur dense_urban vs urban), not a precise census
    # figure - the point is "worldwide and roughly right" replacing the old
    # list's "8 California cities only, everything else guesses rural."
    CITY_DENSITY_TIERS: Dict[str, str] = {
        "Delhi": "dense_urban", "Mumbai": "dense_urban", "Chennai": "dense_urban",
        "Dhaka": "dense_urban", "Chittagong": "dense_urban", "Karachi": "dense_urban",
        "Shanghai": "dense_urban", "Hong Kong": "dense_urban", "Guangzhou": "dense_urban",
        "Singapore": "dense_urban", "Kathmandu": "dense_urban",
        "Bhopal": "urban", "Surat": "urban", "Indore": "urban", "Varanasi": "urban",
        "Jodhpur": "urban", "Amritsar": "urban", "Jaipur": "urban",
        "Beijing": "urban", "Wuhan": "urban", "Changsha": "urban", "Chongqing": "urban",
        "Xi'an": "urban", "Khulna": "urban", "Islamabad": "urban", "Lahore": "urban",
        "Bangkok": "urban", "Ho Chi Minh City": "urban", "Hanoi": "urban",
        "Kuala Lumpur": "urban", "Baghdad": "urban", "Abu Dhabi": "urban",
        "Addis Ababa": "urban", "Nairobi": "urban", "New York": "urban",
        "Los Angeles": "urban", "Houston": "urban",
        "Janakpur": "suburban", "Bhaktapur": "suburban", "Kigali": "suburban",
    }

    @classmethod
    def _haversine_km(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Great-circle distance in km. Raw degree-distance (the old approach
        here) isn't a valid proxy for km: a degree of longitude shrinks
        toward the poles while a degree of latitude doesn't, so the same
        numeric "distance" means a different real distance depending on
        where on Earth it's measured."""
        r_earth_km = 6371.0
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp = math.radians(lat2 - lat1)
        dl = math.radians(lon2 - lon1)
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        return 2 * r_earth_km * math.asin(math.sqrt(a))

    @classmethod
    def _determine_area_type(cls, latitude: float, longitude: float) -> str:
        """
        Determine area type (dense_urban/urban/suburban/rural/very_rural) for
        an incident's coordinates, by proximity to the nearest city TerraGrid
        monitors (CITY_DENSITY_TIERS above) using real great-circle distance.

        This was previously an 8-city, California-only list matched by raw
        degree distance (not real km) - anything outside California fell
        through to a crude distance band instead of an actual density
        estimate, regardless of whether that location was Mumbai or open
        ocean. Still an approximation (TerraGrid has no live census/OSM
        population-density feed), but now at least city-aware worldwide, and
        explicit about its own uncertainty the farther it has to guess.
        """
        try:
            from .openweather import OpenWeatherService
            cities = OpenWeatherService.MONITORED_CITIES
        except ImportError:
            cities = []

        min_distance_km = float("inf")
        nearest_city = None
        for city_lat, city_lon, city_name, _country in cities:
            distance_km = cls._haversine_km(latitude, longitude, city_lat, city_lon)
            if distance_km < min_distance_km:
                min_distance_km = distance_km
                nearest_city = city_name

        nearest_tier = cls.CITY_DENSITY_TIERS.get(nearest_city, "urban") if nearest_city else "urban"

        # Close to a monitored city: use its tier directly. Progressively
        # farther away: step the estimate down toward rural, since density
        # falls off quickly outside a city's built-up area. Past ~80km from
        # any monitored city, this is a genuine guess - "very_rural" is the
        # honest floor rather than continuing to extrapolate a named city's
        # density outward indefinitely.
        if min_distance_km < 15:
            return nearest_tier
        elif min_distance_km < 40:
            return "suburban" if nearest_tier in ("dense_urban", "urban") else nearest_tier
        elif min_distance_km < 80:
            return "rural"
        else:
            return "very_rural"
    
    @classmethod
    def _generate_circle_coordinates(cls, center_lat: float, center_lon: float, 
                                      radius_km: float, num_points: int = 64) -> List[List[float]]:
        """
        Generate coordinates for a circle on map (GeoJSON format)
        
        Args:
            center_lat, center_lon: Center point
            radius_km: Radius in kilometers
            num_points: Number of points to generate (more = smoother circle)
        
        Returns:
            List of [lon, lat] pairs forming a closed polygon
        """
        # Radius in degrees (approximate: 1 degree = 111 km)
        radius_degrees = radius_km / 111.0
        
        coordinates = []
        for i in range(num_points + 1):  # +1 to close the polygon
            angle = (i / num_points) * 2 * math.pi
            lat = center_lat + radius_degrees * math.sin(angle)
            lon = center_lon + radius_degrees * math.cos(angle)
            coordinates.append([lon, lat])  # GeoJSON uses [lon, lat]
        
        return coordinates
    
    @classmethod
    def _calculate_evacuation_times(cls, zones: List[Dict], event_type: str) -> Dict[int, int]:
        """
        Calculate evacuation time for each zone (hours)
        
        Based on:
        - Zone severity
        - Average evacuation speed (30-50 km/h depending on congestion)
        - Event type impact
        """
        # Base evacuation speeds (km/h)
        evacuation_speeds = {
            "earthquake": 40,      # Roads may be damaged, but generally passable
            "fire": 50,            # Higher urgency, faster movement
            "flood": 30,           # Slower due to water hazards
            "hurricane": 35,       # Pre-event evacuation, moderate speed
            "tornado": 50,         # Very high urgency
            "storm": 40,           # Moderate urgency
            "volcano": 40,         # Moderate urgency
            "other": 40,           # Default
        }
        
        speed = evacuation_speeds.get(event_type.lower(), 40)
        
        evacuation_times = {}
        for zone in zones:
            # Time = distance / speed
            # Use max radius as distance
            distance = zone.get("radius_max_km", 5)
            time_hours = max(1, int(distance / speed))  # At least 1 hour
            
            evacuation_times[zone["zone_id"]] = time_hours
        
        return evacuation_times
    
    # Target egress vectors (N, NE, E, SE) approximately 30-40km away
    ROUTE_DIRECTIONS = [
        {"name": "North", "bearing": 0, "lon_offset": 0, "lat_offset": 0.3},
        {"name": "Northeast", "bearing": 45, "lon_offset": 0.25, "lat_offset": 0.25},
        {"name": "East", "bearing": 90, "lon_offset": 0.3, "lat_offset": 0},
        {"name": "Southeast", "bearing": 135, "lon_offset": 0.25, "lat_offset": -0.25},
    ]

    @classmethod
    def _fetch_one_osrm_direction(cls, i: int, lon: float, lat: float, direction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch a single direction's road route from OSRM. Always returns a usable
        route - a real OSRM road geometry when reachable, or a geodesic fallback
        line when OSRM is unreachable/rate-limited. Either way the route list
        comes back complete; this only ever changes HOW accurate one leg is,
        never whether all 4 legs are present.
        """
        import urllib.request
        import json

        dst_lon = lon + direction["lon_offset"] * 2
        dst_lat = lat + direction["lat_offset"] * 2

        route_coords: List[Any] = []
        distance_km = 0.0
        estimated_time_hours = 0.0
        used_real_osrm = False

        try:
            url = f"{cls.OSRM_URL}/driving/{lon},{lat};{dst_lon},{dst_lat}?geometries=geojson&overview=full"
            req = urllib.request.Request(url, headers={'User-Agent': 'TerraGrid-Disaster-App/1.0'})
            with urllib.request.urlopen(req, timeout=3.0) as response:
                data = json.loads(response.read().decode())
                if data.get('code') == 'Ok' and len(data.get('routes', [])) > 0:
                    route_obj = data['routes'][0]
                    route_coords = route_obj['geometry']['coordinates']
                    distance_km = route_obj['distance'] / 1000.0
                    estimated_time_hours = route_obj['duration'] / 3600.0
                    used_real_osrm = True
        except Exception as osrm_err:
            logger.warning(f"[FEATURE_HEALTH] feature=osrm_routing status=fallback direction={direction['name']} error={osrm_err} note=using straight-line geodesic vector instead of a real road route")

        # Fallback to geodesic line if OSRM fails (e.g. over oceans or rate limited)
        if not route_coords:
            route_coords = [[lon, lat], [dst_lon, dst_lat]]
            distance_km = math.sqrt((direction["lon_offset"] * 111)**2 + (direction["lat_offset"] * 111)**2) * 2
            estimated_time_hours = max(1.0, distance_km / 60.0)

        safety_score = min(100, int(80 + distance_km * 0.5))

        return {
            "route_id": f"route_{i}",
            "name": f"Route {i}: {direction['name']} Corridor",
            "direction": direction["name"],
            "distance_km": round(distance_km, 1),
            "estimated_time_hours": round(estimated_time_hours, 1),
            "capacity_vehicles_per_hour": 500 + (i * 100),
            "safety_score": safety_score,
            "coordinates": route_coords,
            "properties": {
                "name": f"Route {i}: {direction['name']}",
                "distance": f"{round(distance_km, 1)} km",
                "time": f"{round(estimated_time_hours, 1)} hours",
                "safety": safety_score,
            },
            "_used_real_osrm": used_real_osrm,
        }

    @classmethod
    @lru_cache(maxsize=128)
    def _cached_safe_routes(cls, rounded_lat: float, rounded_lon: float, event_type: str) -> Tuple[Tuple[Dict[str, Any], ...], int]:
        """
        Computes the 4 evacuation routes and caches the result (coordinates rounded
        to 2 decimal places, ~1km precision, to maximize cache hits on repeat
        requests for the same incident). The 4 OSRM lookups run in parallel -
        they're independent of each other, so there's no reason to wait on them
        one at a time. Returns (routes, real_osrm_count) so the caller can log
        how many of the 4 legs came from real OSRM data vs. a fallback line.
        """
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(cls._fetch_one_osrm_direction, i, rounded_lon, rounded_lat, direction)
                for i, direction in enumerate(cls.ROUTE_DIRECTIONS, 1)
            ]
            routes = [f.result() for f in futures]

        real_osrm_count = sum(1 for r in routes if r.get("_used_real_osrm"))
        for r in routes:
            r.pop("_used_real_osrm", None)

        return tuple(routes), real_osrm_count

    @classmethod
    def get_safe_routes(cls, incident: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identify safe evacuation routes from incident zone using real road networks.

        Args:
            incident: Incident data with coordinates

        Returns:
            routes_data: {
                routes: [
                    {
                        route_id, name, distance_km, safety_score,
                        coordinates: [[lon, lat], ...]
                    }
                ]
            }
        """
        try:
            lat = float(incident.get("latitude", 0))
            lon = float(incident.get("longitude", 0))
            event_type = incident.get("event_type", "other")

            rounded_lat = round(lat, 2)
            rounded_lon = round(lon, 2)

            routes_tuple, real_osrm_count = cls._cached_safe_routes(rounded_lat, rounded_lon, event_type)
            routes = [dict(r) for r in routes_tuple]  # copy so callers can't mutate the cached entries

            result = {
                "incident_id": incident.get("location_name", "Unknown"),
                "incident_center": [lon, lat],
                "routes": routes,
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(f"[FEATURE_HEALTH] feature=osrm_routing status=success routes_generated={len(routes)} real_osrm_routes={real_osrm_count}/{len(routes)} location={incident.get('location_name')}")
            return result

        except Exception as e:
            logger.error(f"[FEATURE_HEALTH] feature=osrm_routing status=error error={type(e).__name__}: {e}")
            return {"error": str(e), "routes": []}
    
    @classmethod
    def get_zone_resources(cls, zone_number: int, population: int) -> Dict[str, Any]:
        """
        Calculate resource requirements for a zone
        
        Args:
            zone_number: Zone 1-4
            population: Population to evacuate
        
        Returns:
            resources: {
                shelters_needed, medical_beds_needed, water_gallons,
                food_meals, vehicles_needed
            }
        """
        try:
            # Resource ratios per person
            shelter_capacity = 5  # sqm per person
            medical_bed_ratio = 0.05  # 1 bed per 20 people
            water_ratio = 3.5  # liters per person per day
            food_ratio = 2  # meals per person per day
            vehicle_capacity = 6  # people per vehicle
            
            # Calculate resources
            resources = {
                "zone": zone_number,
                "population_to_evacuate": population,
                "shelter": {
                    "area_sqm_needed": population * shelter_capacity,
                    "buildings_needed": max(1, int(population / 1000)),
                },
                "medical": {
                    "beds_needed": max(1, int(population * medical_bed_ratio)),
                    "field_hospitals": max(1, int(population / 50000)),
                },
                "water": {
                    "liters_needed": population * water_ratio,
                    "tanker_trucks_needed": max(1, int(population * water_ratio / 10000)),
                },
                "food": {
                    "meals_needed": population * food_ratio,
                    "food_trucks_needed": max(1, int(population * food_ratio / 5000)),
                },
                "transportation": {
                    "vehicles_needed": max(1, int(population / vehicle_capacity)),
                    "buses_needed": max(1, int(population / 50)),
                },
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            return resources
            
        except Exception as e:
            logger.error(f"Error calculating zone resources: {str(e)}")
            return {"error": str(e)}
