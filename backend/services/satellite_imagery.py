"""
Satellite Imagery Fetch Service

Fetches a real satellite image for an incident's coordinates from NASA's
GIBS (Global Imagery Browse Services) WMS - free, public, no API key
required. Used by Feature 11 (Image+Satellite Cross-Validation) to give
Gemini a real image to check an incident report against, instead of
inventing or describing one.

Layer choice: VIIRS_SNPP_CorrectedReflectance_TrueColor is GIBS's
standard true-color daily composite - visible storm clouds, flood
extent, burn scars, smoke plumes are all visible in it. For fire
events we also offer the thermal-anomaly overlay layer, which is more
diagnostic for active fire fronts than true color alone.

Honesty note: if NASA GIBS is unreachable (sandbox network restriction,
NASA outage, etc.), this raises rather than returning a placeholder -
Zero-Mock-Data means we never substitute a fabricated or stock image
for a real satellite pass.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

GIBS_WMS_BASE = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"

# True color is the general-purpose layer; thermal anomalies is a better
# diagnostic specifically for active fires (GIBS' VIIRS Fires/Hotspots layer).
EVENT_TYPE_LAYER = {
    "fire": "VIIRS_SNPP_Thermal_Anomalies_375m_All",
    "wildfire": "VIIRS_SNPP_Thermal_Anomalies_375m_All",
}
DEFAULT_LAYER = "VIIRS_SNPP_CorrectedReflectance_TrueColor"

# Half-width of the bounding box around the incident, in degrees.
# ~0.75 deg is roughly an 80km box at mid-latitudes - wide enough to see
# the disaster's footprint, tight enough to stay legible at 512x512.
BBOX_HALF_DEGREES = 0.75


class SatelliteImageryError(Exception):
    """Raised when a real satellite image genuinely could not be fetched.
    Callers must surface this, never substitute a fabricated image."""


async def fetch_satellite_image(
    latitude: float,
    longitude: float,
    event_type: Optional[str] = None,
    event_timestamp: Optional[datetime] = None,
) -> bytes:
    """
    Fetch a real GIBS satellite image (JPEG bytes) centered on the given
    coordinates, for the date nearest the incident's own timestamp.

    Args:
        latitude, longitude: Incident location (required, real coordinates
            already stored on the Event - never invented here).
        event_type: Used to pick a more diagnostic layer (e.g. thermal
            anomalies for fires) - falls back to true color otherwise.
        event_timestamp: The incident's own real event time. GIBS serves
            daily composites, so we request the matching calendar day.
            Defaults to yesterday if not given, since "today" may not
            have a composite available yet.

    Returns:
        Raw JPEG bytes of the real satellite composite.

    Raises:
        SatelliteImageryError: if GIBS could not be reached or returned
            a non-image response. Never silently substituted.
    """
    layer = EVENT_TYPE_LAYER.get((event_type or "").lower(), DEFAULT_LAYER)

    if event_timestamp:
        request_date = event_timestamp.strftime("%Y-%m-%d")
    else:
        request_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

    bbox = (
        f"{longitude - BBOX_HALF_DEGREES},{latitude - BBOX_HALF_DEGREES},"
        f"{longitude + BBOX_HALF_DEGREES},{latitude + BBOX_HALF_DEGREES}"
    )

    params = {
        "SERVICE": "WMS",
        "VERSION": "1.1.1",
        "REQUEST": "GetMap",
        "LAYERS": layer,
        "SRS": "EPSG:4326",
        "BBOX": bbox,
        "WIDTH": "512",
        "HEIGHT": "512",
        "FORMAT": "image/jpeg",
        "TIME": request_date,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(GIBS_WMS_BASE, params=params)

            content_type = resp.headers.get("content-type", "")
            if resp.status_code != 200 or "image" not in content_type:
                raise SatelliteImageryError(
                    f"GIBS returned {resp.status_code} ({content_type}), "
                    f"not a usable image, for layer={layer} date={request_date}"
                )

            logger.info(
                f"Fetched real GIBS satellite image: layer={layer} "
                f"date={request_date} bbox={bbox} ({len(resp.content)} bytes)"
            )
            return resp.content

    except httpx.HTTPError as e:
        raise SatelliteImageryError(f"GIBS request failed: {type(e).__name__}: {e}") from e
