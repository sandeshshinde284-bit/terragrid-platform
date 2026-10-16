"""
Feature 11: Image+Satellite Cross-Validation

Fetches a real satellite image for an incident's coordinates (via
satellite_imagery.py, NASA GIBS WMS - free, public, no API key) and asks
Gemini's multimodal API to check whether what's actually visible in that
image is consistent with the incident's reported event_type and severity.

This is a real cross-check, not decoration: TerraGrid's incidents come
from source APIs (NASA EONET, GDACS, USGS, NOAA) that can mis-tag
severity or location, or go stale. Having an independent visual read
against a real satellite pass - separate from those same source feeds -
is the actual point of "cross-validation."

Honesty boundaries:
- If the real satellite image can't be fetched, this does NOT fall back
  to a stock photo or a text-only guess - it returns an explicit error
  describing what failed. Faking the image input would make Gemini's
  "visual" assessment fiction.
- If Gemini itself is unavailable (no credentials), returns the same
  is_fallback:true pattern used by DecisionSupportService elsewhere in
  this project, with a plain statement that no visual check was
  performed - never a canned "looks consistent" result.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from backend.config import settings
from .prompt_schemas import SATELLITE_CROSS_VALIDATION_SCHEMA_TEXT
from .satellite_imagery import fetch_satellite_image, SatelliteImageryError

logger = logging.getLogger(__name__)


class SatelliteCrossValidationService:
    """
    Mirrors DecisionSupportService's init pattern: tries to initialize a
    Vertex AI Gemini model capable of multimodal (image + text) input,
    falls back cleanly (never silently) if credentials/SDK are missing.
    """

    def __init__(self):
        self.project_id = settings.GCP_PROJECT_ID
        self.location = settings.GCP_REGION
        self.model = None

        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel

            model_name = settings.GEMINI_MODEL

            if self.project_id:
                vertexai.init(project=self.project_id, location=self.location)
                self.model = GenerativeModel(
                    model_name=model_name,
                    generation_config={"response_mime_type": "application/json"},
                )
                logger.info(
                    f"SatelliteCrossValidationService: Vertex AI {model_name} initialized successfully."
                )
            else:
                logger.warning(
                    "SatelliteCrossValidationService: GCP_PROJECT_ID not configured. Will use fallback."
                )
        except ImportError:
            logger.warning(
                "SatelliteCrossValidationService: google-cloud-aiplatform SDK not installed. Will use fallback."
            )
        except Exception as e:
            logger.warning(
                f"SatelliteCrossValidationService: Could not initialize Vertex AI SDK "
                f"({type(e).__name__}: {e}). Will use fallback."
            )

    async def cross_validate(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """
        Args:
            incident: Must include latitude, longitude, event_type, severity,
                location_name, and optionally event_timestamp (ISO string or
                datetime) - all real fields already on the stored Event.

        Returns:
            Dict with the Gemini visual assessment, OR an honest
            image_fetch_failed / ai_unavailable result - never a fabricated
            "looks fine" placeholder.
        """
        latitude = incident.get("latitude")
        longitude = incident.get("longitude")
        event_type = incident.get("event_type")
        severity = incident.get("severity")
        location_name = incident.get("location_name", "Unknown location")

        if latitude is None or longitude is None:
            return {
                "status": "error",
                "reason": "Incident has no latitude/longitude - cannot fetch a satellite image for a location we don't have.",
            }

        event_timestamp = incident.get("event_timestamp")
        if isinstance(event_timestamp, str):
            try:
                event_timestamp = datetime.fromisoformat(event_timestamp.replace("Z", "+00:00"))
            except ValueError:
                event_timestamp = None
        elif not isinstance(event_timestamp, datetime):
            event_timestamp = None

        # Step 1: fetch a REAL satellite image. No fallback image - if this
        # fails, the whole cross-validation honestly fails too.
        try:
            image_bytes = await fetch_satellite_image(
                latitude=latitude,
                longitude=longitude,
                event_type=event_type,
                event_timestamp=event_timestamp,
            )
        except SatelliteImageryError as e:
            logger.warning(f"[FEATURE_HEALTH] feature=satellite_cross_validation status=image_unavailable location={location_name} error={e}")
            return {
                "status": "image_unavailable",
                "ai_available": False,
                "is_fallback": True,
                "reason": f"Could not fetch a real satellite image: {e}",
                "note": "No cross-validation performed - we do not substitute a stock or fabricated image.",
            }

        # Step 2: ask Gemini to visually assess the REAL image against the
        # reported incident. If Gemini itself isn't available, say so plainly.
        if not self.model:
            logger.info(f"[FEATURE_HEALTH] feature=satellite_cross_validation status=ai_unavailable location={location_name}")
            return {
                "status": "ai_unavailable",
                "ai_available": False,
                "is_fallback": True,
                "image_fetched": True,
                "reason": "Vertex AI Gemini is not configured in this environment - a real satellite image was fetched but no AI visual assessment was performed.",
            }

        try:
            from vertexai.generative_models import Part

            prompt = f"""You are validating a disaster incident report against a real satellite image.

Reported incident:
- Location: {location_name} ({latitude}, {longitude})
- Reported event type: {event_type}
- Reported severity: {severity}

The attached image is a real satellite composite centered on these coordinates,
from the date nearest this incident's report. Look only at what is actually
visible in the image - do not assume the report is correct.

Respond with ONLY this JSON schema, no other text:
{SATELLITE_CROSS_VALIDATION_SCHEMA_TEXT}"""

            image_part = Part.from_data(data=image_bytes, mime_type="image/jpeg")
            response = self.model.generate_content([prompt, image_part])

            import json
            assessment = json.loads(response.text)
            assessment["status"] = "success"
            assessment["ai_available"] = True
            assessment["is_fallback"] = False
            assessment["image_fetched"] = True
            logger.info(f"[FEATURE_HEALTH] feature=satellite_cross_validation status=success location={location_name} visual_consistency={assessment.get('visual_consistency')}")
            return assessment

        except Exception as e:
            logger.error(f"[FEATURE_HEALTH] feature=satellite_cross_validation status=ai_error location={location_name} error={type(e).__name__}: {e}")
            return {
                "status": "ai_error",
                "ai_available": False,
                "is_fallback": True,
                "image_fetched": True,
                "reason": f"A real satellite image was fetched, but the Gemini visual assessment call failed: {type(e).__name__}: {e}",
            }


# Module-level instance, matching the pattern used elsewhere in this project
satellite_cross_validation_service = SatelliteCrossValidationService()
