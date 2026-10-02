"""
Feature 3A: Evacuation Zone Mapping Service
Calculates evacuation zones around disaster incidents
"""
import logging
import math
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta

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
    
    # Population density by area type (people/km²)
    POPULATION_DENSITY = {
        "dense_urban": 10000,
        "urban": 5000,
        "suburban": 2000,
        "rural": 500,
        "very_rural": 100,
    }
    
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
                # Apply severity multiplier
                actual_min = min_radius * multiplier
                actual_max = max_radius * multiplier
                
                # Calculate zone area in km²
                # Area of ring = π(R² - r²)
                area_km2 = math.pi * (actual_max**2 - actual_min**2)
                
                # Estimate population in this zone
                density = cls.POPULATION_DENSITY.get(area_type, 1000)
                population = int(area_km2 * density)
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
            
            logger.info(f"Calculated zones for {location_name}: {total_population} people affected")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating zones: {str(e)}")
            return {"error": str(e), "zones": []}
    
    @classmethod
    def _determine_area_type(cls, latitude: float, longitude: float) -> str:
        """
        Determine area type (urban, suburban, rural) based on coordinates
        
        For MVP, use simplified logic:
        - California coast: urban
        - Major cities: dense_urban
        - Suburban regions: suburban
        - Remote areas: rural
        """
        # Simplified for MVP - could integrate with actual OSM/census data
        
        # CA major cities (lat, lon, type)
        major_cities = [
            (37.7749, -122.4194, "dense_urban"),   # San Francisco
            (34.0522, -118.2437, "dense_urban"),   # Los Angeles
            (32.7157, -117.1611, "dense_urban"),   # San Diego
            (37.3382, -121.8863, "dense_urban"),   # San Jose
            (38.5816, -121.4944, "urban"),         # Sacramento
            (37.9577, -122.3477, "urban"),         # Oakland
            (37.3487, -122.0363, "suburban"),      # San Jose area
            (40.7662, -124.2026, "rural"),         # Eureka
        ]
        
        # Find closest city
        min_distance = float('inf')
        closest_type = "suburban"
        
        for city_lat, city_lon, city_type in major_cities:
            distance = math.sqrt((latitude - city_lat)**2 + (longitude - city_lon)**2)
            if distance < min_distance:
                min_distance = distance
                closest_type = city_type
        
        # Adjust based on distance
        if min_distance < 0.5:
            return closest_type
        elif min_distance < 2:
            return "suburban" if closest_type in ["dense_urban", "urban"] else closest_type
        else:
            return "rural" if min_distance > 5 else "suburban"
    
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
    
    @classmethod
    def get_safe_routes(cls, incident: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identify safe evacuation routes from incident zone
        
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
            
            # Generate mock safe routes (simplified for MVP)
            # Real implementation would use Overpass API or Google Maps
            
            routes = []
            
            # Route directions: N, NE, E, SE, S, SW, W, NW (away from incident)
            directions = [
                {"name": "North", "bearing": 0, "lon_offset": 0, "lat_offset": 0.3},
                {"name": "Northeast", "bearing": 45, "lon_offset": 0.25, "lat_offset": 0.25},
                {"name": "East", "bearing": 90, "lon_offset": 0.3, "lat_offset": 0},
                {"name": "Southeast", "bearing": 135, "lon_offset": 0.25, "lat_offset": -0.25},
            ]
            
            for i, direction in enumerate(directions, 1):
                # Create route coordinates
                route_coords = [
                    [lon, lat],  # Start at incident center
                    [lon + direction["lon_offset"] * 2, lat + direction["lat_offset"] * 2],  # 30km away
                ]
                
                # Calculate safety score (0-100)
                # Score based on distance from incident center
                distance_km = math.sqrt(
                    (direction["lon_offset"] * 111)**2 + 
                    (direction["lat_offset"] * 111)**2
                ) * 2
                
                safety_score = min(100, int(80 + distance_km * 2))
                
                route = {
                    "route_id": f"route_{i}",
                    "name": f"Route {i}: {direction['name']} Corridor",
                    "direction": direction["name"],
                    "distance_km": round(distance_km, 1),
                    "estimated_time_hours": max(1, int(distance_km / 60)),
                    "capacity_vehicles_per_hour": 500 + (i * 100),
                    "safety_score": safety_score,
                    "coordinates": route_coords,
                    "properties": {
                        "name": f"Route {i}: {direction['name']}",
                        "distance": f"{round(distance_km, 1)} km",
                        "time": f"{max(1, int(distance_km / 60))} hours",
                        "safety": safety_score,
                    }
                }
                routes.append(route)
            
            result = {
                "incident_id": incident.get("location_name", "Unknown"),
                "incident_center": [lon, lat],
                "routes": routes,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            logger.info(f"Generated {len(routes)} safe routes for {incident.get('location_name')}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating safe routes: {str(e)}")
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
