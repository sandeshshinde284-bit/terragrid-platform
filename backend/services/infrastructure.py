from backend.config import settings
import urllib.request
import urllib.parse
import json
import logging
import math
from typing import List, Dict, Any
from functools import lru_cache
import os
import socket
from backend.utils.data_logger import log_raw_data

logger = logging.getLogger(__name__)

class InfrastructureService:
    """
    Queries OpenStreetMap (via Overpass API) to find real-world physical
    infrastructure (hospitals, fire stations, schools, power grids, bridges).
    Provides hard GIS data to Vertex AI to prevent hallucination.
    Includes LRU caching to prevent Overpass API rate limits.
    
    **NOTE:** Overpass API is frequently overloaded/rate-limited. Failures are
    gracefully handled by returning empty results (non-blocking).
    """
    OVERPASS_URL = settings.OVERPASS_API_URL
    OVERPASS_TIMEOUT = settings.OVERPASS_API_TIMEOUT  # Increased from 8s (Overpass API is slow)
    OVERPASS_RETRIES = settings.OVERPASS_API_RETRIES   # Increased from 2 retries
    # Parsed once at class-load time from the comma-separated OVERPASS_API_MIRRORS
    # setting. Falls back to the single OVERPASS_URL if mirrors aren't configured
    # (e.g. an older .env that predates this setting), so this never ends up empty.
    OVERPASS_MIRRORS = [u.strip() for u in settings.OVERPASS_API_MIRRORS.split(',') if u.strip()] or [OVERPASS_URL]

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate the great circle distance between two points on the earth in km."""
        R = 6371.0 # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2)**2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @classmethod
    @lru_cache(maxsize=128)
    def _cached_overpass_query(cls, rounded_lat: float, rounded_lon: float, radius_m: int) -> Dict[str, Any]:
        """
        Executes and caches the Overpass query with retry logic.
        Coordinates are rounded to 2 decimal places (~1km precision) to maximize cache hits.
        Returns empty dict on timeout/failure (non-blocking).
        """
        query = f"""
        [out:json][timeout:5];
        (
          node["amenity"="hospital"](around:{radius_m},{rounded_lat},{rounded_lon});
          node["amenity"="fire_station"](around:{radius_m},{rounded_lat},{rounded_lon});
          node["amenity"="school"](around:{radius_m},{rounded_lat},{rounded_lon});
          way["amenity"="hospital"](around:{radius_m},{rounded_lat},{rounded_lon});
          
          node["power"="substation"](around:{radius_m},{rounded_lat},{rounded_lon});
          node["power"="plant"](around:{radius_m},{rounded_lat},{rounded_lon});
          node["man_made"="water_treatment_plant"](around:{radius_m},{rounded_lat},{rounded_lon});
          way["bridge"="yes"](around:{radius_m},{rounded_lat},{rounded_lon});
        );
        out center 25;
        """
        
        data = urllib.parse.urlencode({'data': query}).encode('utf-8')

        # Retry logic for transient failures with exponential backoff.
        # Each attempt rotates to the next mirror in OVERPASS_MIRRORS (wrapping
        # around if there are more retries than mirrors) instead of retrying the
        # same host - overpass-api.de getting a 502 under load says nothing about
        # whether overpass.kumi.systems or overpass.openstreetmap.ru are up, since
        # these are independently-run public servers.
        last_error = None
        for attempt in range(cls.OVERPASS_RETRIES):
            url = cls.OVERPASS_MIRRORS[attempt % len(cls.OVERPASS_MIRRORS)]
            req = urllib.request.Request(url, data=data, headers={'User-Agent': 'TerraGrid-Disaster-App/1.0'})
            try:
                logger.debug(f"[OSM] Attempt {attempt + 1}/{cls.OVERPASS_RETRIES} to query Overpass mirror {url} (timeout={cls.OVERPASS_TIMEOUT}s)")
                with urllib.request.urlopen(req, timeout=cls.OVERPASS_TIMEOUT) as response:
                    result = json.loads(response.read().decode())
                    logger.debug(f"[OSM] Query succeeded via {url}: {len(result.get('elements', []))} elements found")
                    # Note: this method is @lru_cache'd, so this only fires on
                    # an actual fetch, not on a cache hit for the same
                    # rounded lat/lon/radius - that's fine, it's the live
                    # Overpass response that needs cross-checking.
                    log_raw_data("osm", result, label="overpass_raw", context={"lat": rounded_lat, "lon": rounded_lon, "radius_m": radius_m, "mirror": url})
                    return result
            except (socket.timeout, urllib.error.URLError, TimeoutError) as e:
                last_error = e
                logger.debug(f"[OSM] Attempt {attempt + 1} via {url} failed: {type(e).__name__}: {e}")
                if attempt < cls.OVERPASS_RETRIES - 1:
                    # Exponential backoff with jitter: 2s, 4s, 8s (plus random 0-1s).
                    # Kept even though the next attempt hits a different mirror -
                    # it also covers the case where OUR network/egress is the one
                    # having a transient issue, not the remote server.
                    import time
                    import random
                    wait_time = (2 ** (attempt + 1)) + random.uniform(0, 1)
                    logger.debug(f"[OSM] Waiting {wait_time:.1f}s before retry {attempt + 2}...")
                    time.sleep(wait_time)
            except Exception as e:
                # Other errors (JSON parse, connection reset, etc.) - don't retry
                logger.warning(f"[OSM] Non-retriable error via {url}: {type(e).__name__}: {e}")
                return {"elements": []}
        
        # All retries exhausted (across all mirrors tried)
        logger.warning(f"[FEATURE_HEALTH] feature=osm_overpass status=all_retries_failed attempts={cls.OVERPASS_RETRIES} mirrors_tried={cls.OVERPASS_MIRRORS[:cls.OVERPASS_RETRIES]} error={last_error}")
        log_raw_data("osm", {"elements": [], "error": str(last_error)}, label="overpass_failed", context={"lat": rounded_lat, "lon": rounded_lon, "radius_m": radius_m, "attempts": cls.OVERPASS_RETRIES, "mirrors_tried": cls.OVERPASS_MIRRORS[:cls.OVERPASS_RETRIES]})
        return {"elements": []}  # Return empty result, don't block response

    @classmethod
    def get_nearby_facilities(cls, lat: float, lon: float, radius_km: float = 20.0) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetches physical infrastructure within the radius, categorized by type.
        
        **IMPORTANT:** This method is designed to be non-blocking. If Overpass API
        times out or fails, it returns empty results rather than blocking the response.
        This allows the AI dossier to still be generated even without OSM data.
        """
        clamped_radius_m = int(max(5.0, min(50.0, radius_km)) * 1000)
        
        results = {
            "hospitals": [],
            "fire_stations": [],
            "shelters": [], # Schools used as proxies for emergency shelters
            "critical_infrastructure": [] # Power grids, water plants, bridges
        }
        
        try:
            # Round coordinates to 2 decimal places to maximize cache hits
            rounded_lat = round(lat, 2)
            rounded_lon = round(lon, 2)
            
            res_data = cls._cached_overpass_query(rounded_lat, rounded_lon, clamped_radius_m)
            
            for element in res_data.get('elements', []):
                tags = element.get('tags', {})
                name = tags.get('name')
                
                # Try to get a name, if it's a bridge without a name, label it as "Highway Bridge"
                if not name:
                    if tags.get('bridge') == 'yes':
                        name = "Highway Bridge Segment"
                    else:
                        continue
                    
                amenity = tags.get('amenity', 'unknown')
                power = tags.get('power', '')
                man_made = tags.get('man_made', '')
                bridge = tags.get('bridge', '')
                
                f_lat = element.get('lat') or element.get('center', {}).get('lat')
                f_lon = element.get('lon') or element.get('center', {}).get('lon')
                
                if f_lat and f_lon:
                    dist = cls._haversine(lat, lon, f_lat, f_lon)
                    facility = {
                        'name': name,
                        'distance_km': round(dist, 1)
                    }
                    
                    if amenity == 'hospital':
                        results["hospitals"].append(facility)
                    elif amenity == 'fire_station':
                        results["fire_stations"].append(facility)
                    elif amenity == 'school':
                        results["shelters"].append(facility)
                    elif power in ['substation', 'plant']:
                        facility['type'] = 'Power Facility'
                        results["critical_infrastructure"].append(facility)
                    elif man_made == 'water_treatment_plant':
                        facility['type'] = 'Water Treatment Plant'
                        results["critical_infrastructure"].append(facility)
                    elif bridge == 'yes':
                        facility['type'] = 'Bridge'
                        results["critical_infrastructure"].append(facility)
                        
            # Sort by distance and limit to top 5 per category
            for key in results:
                results[key] = sorted(results[key], key=lambda x: x['distance_km'])[:5]
                
            if any([results['hospitals'], results['fire_stations'], results['critical_infrastructure'], results['shelters']]):
                logger.info(f"[FEATURE_HEALTH] feature=osm_overpass status=success hospitals={len(results['hospitals'])} fire_stations={len(results['fire_stations'])} critical_infrastructure={len(results['critical_infrastructure'])} location=({lat}, {lon})")
            else:
                logger.debug(f"[OSM] No infrastructure found near {lat}, {lon} (this is OK - OSM may not have data for remote areas)")
            
            return results
            
        except Exception as e:
            # Non-blocking failure: log and return empty results
            logger.warning(f"[FEATURE_HEALTH] feature=osm_overpass status=error error={type(e).__name__}: {e}")
            return results  # Return empty dict, don't crash