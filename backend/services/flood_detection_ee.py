"""
Feature 13: Sentinel-1 SAR Flood Detection via Google Earth Engine

Implements the published Sentinel-1 backscatter change-detection method
for flood mapping - the same method documented as UN-SPIDER's official
"Recommended Practice: Flood Mapping and Damage Assessment Using
Sentinel-1 SAR Data in Google Earth Engine"
(https://un-spider.org/advisory-support/recommended-practices/recommended-practice-google-earth-engine-flood-mapping/step-by-step),
itself based on DeVries et al., Remote Sensing of Environment (2020).

UN-SPIDER only publishes this as a JavaScript Earth Engine Code Editor
script - there is no official Python port. This module is a from-scratch
port to the Earth Engine Python API, following the same published steps:

  1. Pre-flood / post-flood Sentinel-1 GRD composites (same orbit pass,
     to avoid false positives from viewing-angle differences)
  2. Backscatter change: post vs. pre comparison
  3. JRC Global Surface Water mask (permanent water removed)
  4. HydroSHEDS/SRTM slope mask (>5% slope removed - unlikely flood terrain)
  5. Connectivity filter (isolated noise pixels removed)
  6. Flood area computed from the surviving pixels, in real km^2

One ambiguity in the published method, resolved here and documented
honestly rather than guessed silently: the page does not say whether its
"ratio > 1.25" threshold is computed on dB or linear backscatter values.
Sentinel-1 GRD bands in Earth Engine are already in dB. A linear ratio
of 1.25 is equivalent to a dB difference of 10*log10(1.25) ~= 0.9691 dB,
so this implementation thresholds the dB difference directly at that
value - mathematically the same comparison, just computed in the units
the data actually arrives in.

Zero-Mock-Data discipline: every dataset here is real and public
(Sentinel-1 GRD, JRC Global Surface Water, SRTM DEM). If Earth Engine
isn't authenticated, or the area has no usable Sentinel-1 coverage for
the requested dates, this raises/returns an explicit failure - it never
fabricates a flood polygon or a plausible-sounding area figure.
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from backend.config import settings

logger = logging.getLogger(__name__)

# 1.25 linear ratio (UN-SPIDER's published threshold), converted to the
# equivalent dB difference since GEE's Sentinel-1 GRD bands are in dB.
DB_CHANGE_THRESHOLD = 10 * math.log10(1.25)  # ~= 0.9691 dB

# JRC Global Surface Water: pixels wet more than this many months/year,
# on average, are treated as permanent water and masked out (per UN-SPIDER).
PERMANENT_WATER_MONTHS_THRESHOLD = 10

# Terrain slope above this percent is excluded - flooding on steep slopes
# is physically implausible and usually a SAR layover/shadow artifact.
MAX_SLOPE_PERCENT = 5

# Connectivity filter: flood pixels connected to this many or fewer
# same-value neighbors are treated as speckle noise and removed.
MIN_CONNECTED_PIXELS = 8

# Bounding box half-width in degrees around the incident, matching
# satellite_imagery.py's footprint so both features look at a
# comparable area (~80km box at mid-latitudes).
AOI_HALF_DEGREES = 0.75


class FloodDetectionError(Exception):
    """Raised when a real flood analysis genuinely could not be computed -
    never papered over with a fabricated or placeholder result."""


class EarthEngineFloodDetectionService:
    """
    Wraps the Earth Engine Python API with the same init/fallback pattern
    used elsewhere in this project (DecisionSupportService, VectorRAGEngine,
    SatelliteCrossValidationService): try real auth, degrade honestly if
    unavailable, never silently substitute fake output.
    """

    def __init__(self):
        self.project_id = settings.GCP_PROJECT_ID
        self.initialized = False

        try:
            import ee
            import google.auth

            # Uses the same GOOGLE_APPLICATION_CREDENTIALS the rest of this
            # project's Vertex AI services rely on - the service account
            # just additionally needs Earth Engine access granted (via the
            # noncommercial registration), not a separate credential file.
            credentials, _ = google.auth.default(
                scopes=[
                    "https://www.googleapis.com/auth/earthengine",
                    "https://www.googleapis.com/auth/cloud-platform",
                ]
            )
            ee.Initialize(credentials, project=self.project_id)
            self.initialized = True
            logger.info("EarthEngineFloodDetectionService: Earth Engine initialized successfully.")

        except ImportError:
            logger.warning(
                "EarthEngineFloodDetectionService: earthengine-api not installed. Flood detection unavailable."
            )
        except Exception as e:
            logger.warning(
                f"EarthEngineFloodDetectionService: Could not initialize Earth Engine "
                f"({type(e).__name__}: {e}). Flood detection unavailable."
            )

    def detect_flood(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """
        Args:
            incident: Must include latitude, longitude, location_name, and
                event_timestamp (datetime or ISO string) - all real,
                already-stored Event fields.

        Returns:
            Dict with the real computed flood area and methodology details,
            OR an honest unavailable/error result. Never a fabricated area.
        """
        if not self.initialized:
            return {
                "status": "ee_unavailable",
                "ai_available": False,
                "is_fallback": True,
                "reason": (
                    "Earth Engine is not authenticated in this environment "
                    "(needs GOOGLE_APPLICATION_CREDENTIALS plus Earth Engine "
                    "access on that service account). No flood analysis performed."
                ),
            }

        latitude = incident.get("latitude")
        longitude = incident.get("longitude")
        location_name = incident.get("location_name", "Unknown location")
        event_timestamp = incident.get("event_timestamp")

        if latitude is None or longitude is None:
            return {"status": "error", "reason": "Incident has no latitude/longitude."}

        if isinstance(event_timestamp, str):
            try:
                event_timestamp = datetime.fromisoformat(event_timestamp.replace("Z", "+00:00"))
            except ValueError:
                event_timestamp = None
        if not isinstance(event_timestamp, datetime):
            event_timestamp = datetime.utcnow()

        try:
            return self._run_analysis(latitude, longitude, location_name, event_timestamp)
        except FloodDetectionError as e:
            logger.warning(f"Flood detection failed for {location_name}: {e}")
            return {
                "status": "analysis_failed",
                "ai_available": False,
                "is_fallback": True,
                "reason": str(e),
            }
        except Exception as e:
            logger.error(f"Unexpected Earth Engine error for {location_name}: {type(e).__name__}: {e}")
            return {
                "status": "ee_error",
                "ai_available": False,
                "is_fallback": True,
                "reason": f"{type(e).__name__}: {e}",
            }

    def _run_analysis(
        self, latitude: float, longitude: float, location_name: str, event_timestamp: datetime
    ) -> Dict[str, Any]:
        """The actual Earth Engine computation. Synchronous/blocking by
        nature of the ee client - callers should run this in a thread."""
        import ee

        aoi = ee.Geometry.Rectangle([
            longitude - AOI_HALF_DEGREES,
            latitude - AOI_HALF_DEGREES,
            longitude + AOI_HALF_DEGREES,
            latitude + AOI_HALF_DEGREES,
        ])

        # Pre-flood window: a month-long baseline ending well before the
        # event, so it doesn't itself catch early flood onset.
        pre_end = event_timestamp - timedelta(days=12)
        pre_start = pre_end - timedelta(days=24)
        # Post-flood window: starting at the event, extending far enough to
        # likely catch at least one Sentinel-1 pass (12-day revisit cycle).
        post_start = event_timestamp - timedelta(days=1)
        post_end = event_timestamp + timedelta(days=13)

        s1 = (
            ee.ImageCollection("COPERNICUS/S1_GRD")
            .filterBounds(aoi)
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
            .select("VV")
        )

        pre_collection = s1.filterDate(pre_start.isoformat(), pre_end.isoformat())
        post_collection = s1.filterDate(post_start.isoformat(), post_end.isoformat())

        # UN-SPIDER's guidance: pre/post must use the same orbit pass
        # direction to avoid false positives from viewing-angle differences.
        # Pick whichever direction has coverage in BOTH windows.
        orbit_direction = self._pick_common_orbit(pre_collection, post_collection)
        if orbit_direction is None:
            raise FloodDetectionError(
                f"No Sentinel-1 coverage with a common orbit pass found for "
                f"{location_name} in the pre-flood ({pre_start.date()} to {pre_end.date()}) "
                f"and post-flood ({post_start.date()} to {post_end.date()}) windows."
            )

        pre_filtered = pre_collection.filter(ee.Filter.eq("orbitProperties_pass", orbit_direction))
        post_filtered = post_collection.filter(ee.Filter.eq("orbitProperties_pass", orbit_direction))

        pre_count = pre_filtered.size().getInfo()
        post_count = post_filtered.size().getInfo()
        if pre_count == 0 or post_count == 0:
            raise FloodDetectionError(
                f"Sentinel-1 orbit filtering left no usable images "
                f"(pre={pre_count}, post={post_count}) for {location_name}."
            )

        # Speckle reduction via median compositing (multiple looks) plus a
        # focal median smoothing filter, matching UN-SPIDER's circular
        # smoothing step.
        pre_composite = pre_filtered.median().focal_median(50, "circle", "meters")
        post_composite = post_filtered.median().focal_median(50, "circle", "meters")

        # Change detection. Bands are already in dB, so a dB difference
        # above DB_CHANGE_THRESHOLD is equivalent to UN-SPIDER's linear
        # ratio > 1.25 (see module docstring).
        db_diff = post_composite.subtract(pre_composite)
        flood_candidate = db_diff.gt(DB_CHANGE_THRESHOLD)

        # Mask 1: permanent water (JRC Global Surface Water)
        gsw = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("seasonality")
        permanent_water = gsw.gte(PERMANENT_WATER_MONTHS_THRESHOLD)
        flood_candidate = flood_candidate.updateMask(permanent_water.Not())

        # Mask 2: steep slopes (SRTM DEM)
        dem = ee.Image("USGS/SRTMGL1_003")
        slope_percent = ee.Terrain.slope(dem)
        flood_candidate = flood_candidate.updateMask(slope_percent.lt(MAX_SLOPE_PERCENT))

        # Mask 3: connectivity filter (remove isolated noise pixels)
        connections = flood_candidate.selfMask().connectedPixelCount(MIN_CONNECTED_PIXELS + 1, True)
        flood_mask = flood_candidate.updateMask(connections.gt(MIN_CONNECTED_PIXELS))

        # Real area computation over the AOI, not an estimate.
        pixel_area = ee.Image.pixelArea()
        flood_area_m2 = pixel_area.updateMask(flood_mask).reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=aoi,
            scale=10,  # Sentinel-1 GRD native resolution
            maxPixels=1e9,
        ).get("area")

        flood_area_m2_value = flood_area_m2.getInfo() if flood_area_m2 is not None else 0
        flood_area_hectares = round((flood_area_m2_value or 0) / 10000, 2)
        flood_area_km2 = round((flood_area_m2_value or 0) / 1_000_000, 3)

        return {
            "status": "success",
            "ai_available": True,
            "is_fallback": False,
            "location_name": location_name,
            "flood_area_hectares": flood_area_hectares,
            "flood_area_km2": flood_area_km2,
            "methodology": (
                "Sentinel-1 VV backscatter change detection (post vs. pre composite, "
                "same orbit pass), dB-difference threshold equivalent to a 1.25 "
                "linear ratio, masked against JRC Global Surface Water (permanent "
                "water) and SRTM slope (>5%), connectivity-filtered. Ported from "
                "UN-SPIDER's published Earth Engine Code Editor methodology "
                "(itself based on DeVries et al., Remote Sensing of Environment, 2020)."
            ),
            "orbit_pass_used": orbit_direction,
            "pre_flood_window": f"{pre_start.date()} to {pre_end.date()} ({pre_count} images)",
            "post_flood_window": f"{post_start.date()} to {post_end.date()} ({post_count} images)",
            "db_change_threshold": round(DB_CHANGE_THRESHOLD, 4),
        }

    @staticmethod
    def _pick_common_orbit(pre_collection, post_collection) -> Optional[str]:
        """Returns 'ASCENDING' or 'DESCENDING', whichever has images in
        BOTH the pre- and post-flood windows, or None if neither does."""
        import ee

        for direction in ("ASCENDING", "DESCENDING"):
            pre_has = pre_collection.filter(
                ee.Filter.eq("orbitProperties_pass", direction)
            ).size().getInfo()
            post_has = post_collection.filter(
                ee.Filter.eq("orbitProperties_pass", direction)
            ).size().getInfo()
            if pre_has > 0 and post_has > 0:
                return direction
        return None


# Module-level instance, matching the pattern used elsewhere in this project
flood_detection_service = EarthEngineFloodDetectionService()
