from backend.config import settings
"""
API Routes for PREPARE phase features (PR1, PR7, PR2, PR6, PR4)

PR1: 7-Day Forecast Dashboard
Fetches live 5-day/3-hour-step forecasts from OpenWeatherMap (same API key and
MONITORED_CITIES already used for current-weather ingestion) and collapses them
into a per-city, per-day risk escalation timeline (GREEN/YELLOW/ORANGE/RED).
No other external API is called for this feature.
"""
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
import asyncio
import logging
from datetime import datetime

from ..services import OpenWeatherService
from ..services.decision_support import get_decision_support_service
from ..services.whatsapp import get_whatsapp_service
from ..services.notifications import notification_service
from ..services.evacuation_zones import EvacuationZoneService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/prepare", tags=["prepare"])


# PR1: 7-Day Forecast Dashboard
@router.get("/forecast")
async def get_forecast(use_mock: bool = Query(False, description="Use mock data for testing")):
    """
    PR1: Fetch the 5-day/3-hour-step OpenWeatherMap forecast for all monitored
    cities, summarized into one risk-escalation entry per day.

    Returns:
        - Per-city list, each with a "daily" timeline of
          {date, risk_level, dominant_weather, max_wind_ms, min_temp_c, max_temp_c, total_rain_mm}
    """
    try:
        forecasts = await OpenWeatherService.fetch_forecast(use_mock=use_mock)

        return {
            "status": "success",
            "source": "OpenWeatherMap (/data/2.5/forecast)",
            "city_count": len(forecasts),
            "data": forecasts,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Forecast fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# PR2: Preparedness Action Generator
@router.get("/actions")
async def get_preparedness_actions(
    city: str = Query(..., description="City name, matching PR1's forecast output"),
    country: str = Query("", description="ISO2 country code, matching PR1's forecast output"),
    use_mock: bool = Query(False, description="Use mock data for testing"),
):
    """
    PR2: Generate an AI preparedness checklist (clear drains, stock supplies,
    alert hospitals, position boats, etc.) for one city, tied to that city's
    5-day risk escalation forecast from PR1.

    Returns:
        - risk_context: 1-2 sentence summary of what's driving the checklist
        - actions: list of {action, agency, category, priority, deadline_day, rationale}
        - ai_available / is_fallback / is_mock_demo: transparent provenance flags
    """
    try:
        forecasts = await OpenWeatherService.fetch_forecast(use_mock=use_mock)

        city_forecast = next(
            (
                f for f in forecasts
                if f.get("city", "").lower() == city.lower()
                and (not country or f.get("country", "").lower() == country.lower())
            ),
            None,
        )

        if not city_forecast:
            raise HTTPException(
                status_code=404,
                detail=f"No forecast found for city='{city}' country='{country}'. "
                       f"Fetch /api/v1/prepare/forecast first to see available cities.",
            )

        service = get_decision_support_service()
        actions_plan = service.generate_preparedness_actions(city_forecast, use_mock=use_mock)

        return {
            "status": "success",
            "city": city_forecast.get("city"),
            "country": city_forecast.get("country"),
            "source": (
                "Mock demonstration data" if actions_plan.get("is_mock_demo")
                else "Gemini 2.5 Flash via Vertex AI" if actions_plan.get("ai_available")
                else "Offline fallback checklist"
            ),
            "data": actions_plan,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preparedness action generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# PR5: Evacuation Route Pre-Calculation
#
# Why gate on PR9's alert_recommended rather than any non-GREEN day: the
# existing get_safe_routes() call hits the real OSRM routing engine (4
# directions x up to 3s each) - worth paying that cost once risk is both
# elevated AND well-supported across the day's forecast entries, not for
# every city on every poll, and not for a single isolated 3-hour spike
# that PR9 already tells us not to alert on.
RISK_RANK = {"GREEN": 0, "YELLOW": 1, "ORANGE": 2, "RED": 3}

# OpenWeatherMap's own "weather.main" labels (already used as-is for
# display in PR1/PR7) mapped to the event_type categories
# EvacuationZoneService/get_safe_routes was built around. This only
# affects display/labeling in the response - get_safe_routes' own routing
# call doesn't branch on event_type - but an honest label matters so the
# response doesn't claim a disaster type the forecast didn't say.
WEATHER_TO_EVENT_TYPE = {
    "thunderstorm": "storm",
    "squall": "storm",
    "tornado": "tornado",
    "rain": "flood",
    "drizzle": "flood",
    "snow": "storm",
}


@router.get("/evacuation-routes")
async def get_evacuation_routes(
    city: str = Query(..., description="City name, matching PR1's forecast output"),
    country: str = Query("", description="ISO2 country code, matching PR1's forecast output"),
    use_mock: bool = Query(False, description="Use mock data for testing"),
):
    """
    PR5: Proactively pre-calculate safe evacuation routes for a city once
    its 5-day forecast crosses into an elevated AND well-supported risk
    level (PR9's alert_recommended), instead of only computing routes
    reactively after an incident already exists.

    Reuses RESPONSE phase's real OSRM-routed egress corridors
    (EvacuationZoneService.get_safe_routes) - no separate PREPARE-specific
    routing logic, no fabricated routes.

    Returns:
        - status: "success" (routes computed) or "not_needed" (no
          forecast day both cleared the risk and confidence bar)
        - qualifying_day: the forecast day that triggered pre-calculation
          (None when status is "not_needed")
        - routes: real OSRM-routed egress corridors, or [] when not_needed
    """
    try:
        forecasts = await OpenWeatherService.fetch_forecast(use_mock=use_mock)

        city_forecast = next(
            (
                f for f in forecasts
                if f.get("city", "").lower() == city.lower()
                and (not country or f.get("country", "").lower() == country.lower())
            ),
            None,
        )

        if not city_forecast:
            raise HTTPException(
                status_code=404,
                detail=f"No forecast found for city='{city}' country='{country}'. "
                       f"Fetch /api/v1/prepare/forecast first to see available cities.",
            )

        daily = city_forecast.get("daily", [])
        qualifying_days = [d for d in daily if d.get("alert_recommended")]

        if not qualifying_days:
            return {
                "status": "not_needed",
                "city": city_forecast.get("city"),
                "country": city_forecast.get("country"),
                "reason": (
                    "No forecast day for this city is both at elevated risk and "
                    "confident enough (see PR9's confidence_pct/alert_recommended) "
                    "to justify pre-calculating evacuation routes."
                ),
                "qualifying_day": None,
                "routes": [],
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Among qualifying days, the worst one drives the route's displayed
        # event type - lat/lon don't vary by day, only which day justified
        # computing the routes at all.
        worst_day = max(qualifying_days, key=lambda d: RISK_RANK.get(d.get("risk_level"), 0))
        event_type = WEATHER_TO_EVENT_TYPE.get((worst_day.get("dominant_weather") or "").lower(), "other")

        incident = {
            "latitude": city_forecast.get("latitude"),
            "longitude": city_forecast.get("longitude"),
            "event_type": event_type,
            "location_name": city_forecast.get("city"),
        }

        # get_safe_routes() makes blocking HTTP calls to OSRM (up to 4 x 3s
        # timeout) - run it off the event loop so one slow pre-calculation
        # doesn't stall every other request this server is handling.
        routes_data = await asyncio.to_thread(EvacuationZoneService.get_safe_routes, incident)

        if routes_data.get("error"):
            raise HTTPException(status_code=502, detail=routes_data["error"])

        return {
            "status": "success",
            "city": city_forecast.get("city"),
            "country": city_forecast.get("country"),
            "qualifying_day": {
                "date": worst_day.get("date"),
                "risk_level": worst_day.get("risk_level"),
                "confidence_pct": worst_day.get("confidence_pct"),
                "dominant_weather": worst_day.get("dominant_weather"),
                "event_type": event_type,
            },
            "routes": routes_data.get("routes", []),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Evacuation route pre-calculation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# PR4: Agency Alert Templates
@router.get("/alerts")
async def get_agency_alerts(
    city: str = Query(..., description="City name, matching PR1's forecast output"),
    country: str = Query("", description="ISO2 country code, matching PR1's forecast output"),
    use_mock: bool = Query(False, description="Use mock data for testing"),
):
    """
    PR4: Generate distinct, audience-appropriate alert templates (farmers,
    hospitals, NGOs, municipal corps) for one city, tied to that city's 5-day
    risk escalation forecast from PR1 - not one generic broadcast reused for
    every audience.

    Returns:
        - risk_context: 1-2 sentence summary of what's driving the alerts
        - alerts: list of {audience, channel, headline, message, tone_rationale}
        - ai_available / is_fallback / is_mock_demo: transparent provenance flags
    """
    try:
        forecasts = await OpenWeatherService.fetch_forecast(use_mock=use_mock)

        city_forecast = next(
            (
                f for f in forecasts
                if f.get("city", "").lower() == city.lower()
                and (not country or f.get("country", "").lower() == country.lower())
            ),
            None,
        )

        if not city_forecast:
            raise HTTPException(
                status_code=404,
                detail=f"No forecast found for city='{city}' country='{country}'. "
                       f"Fetch /api/v1/prepare/forecast first to see available cities.",
            )

        service = get_decision_support_service()
        alerts_plan = service.generate_agency_alerts(city_forecast, use_mock=use_mock)

        return {
            "status": "success",
            "city": city_forecast.get("city"),
            "country": city_forecast.get("country"),
            "source": (
                "Mock demonstration data" if alerts_plan.get("is_mock_demo")
                else "Gemini 2.5 Flash via Vertex AI" if alerts_plan.get("ai_available")
                else "Offline fallback alert"
            ),
            "data": alerts_plan,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agency alert generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# PR4 extension: manual WhatsApp send for Agency Alerts, via WAHA.
# Scope: manual only - an operator reviews the AI-drafted text, picks a
# pre-approved demo recipient, and clicks Send. No automated/threshold-
# triggered sending here (see PREPARE_PHASE_NOTES.md for that as a
# separate, larger feature).

@router.get("/alerts/recipients")
async def get_whatsapp_recipients():
    """
    Pre-approved demo WhatsApp recipients (from WHATSAPP_RECIPIENTS env var),
    for the frontend's recipient picker. Deliberately not arbitrary - see
    WhatsAppService's docstring for why sends are restricted to this list.
    """
    service = get_whatsapp_service()
    return {
        "status": "success",
        "configured": service.is_configured,
        "recipients": service.get_recipients(),
    }


class SendWhatsAppAlertRequest(BaseModel):
    phone_number: str
    message: str


@router.post("/alerts/send")
async def send_whatsapp_alert(payload: SendWhatsAppAlertRequest):
    """
    Sends an already-drafted Agency Alert message to one pre-approved demo
    WhatsApp recipient via WAHA. The frontend sends the exact message text
    the operator reviewed on screen - this route does not regenerate or
    alter it.
    """
    service = get_whatsapp_service()
    result = await service.send_text(payload.phone_number, payload.message)

    if not result["success"]:
        raise HTTPException(status_code=502, detail=result["detail"])

    return {
        "status": "success",
        "detail": result["detail"],
    }


# PR4 extension: manual email send for Agency Alerts, via Resend. Same
# scope and allowlist reasoning as the WhatsApp send above - a fixed,
# pre-approved demo recipient list (EMAIL_ALERT_RECIPIENTS), manual only.

@router.get("/alerts/email-recipients")
async def get_email_alert_recipients():
    """
    Pre-approved demo email recipients (from EMAIL_ALERT_RECIPIENTS env
    var), for the frontend's email recipient picker.
    """
    return {
        "status": "success",
        "configured": notification_service.is_configured,
        "recipients": notification_service.get_alert_email_recipients(),
    }


class SendEmailAlertRequest(BaseModel):
    email: str
    subject: str
    message: str


@router.post("/alerts/send-email")
async def send_email_alert(payload: SendEmailAlertRequest):
    """
    Sends an already-drafted Agency Alert message to one pre-approved demo
    email recipient via Resend. The frontend sends the exact subject/body
    the operator reviewed on screen - this route does not regenerate it.
    """
    result = notification_service.send_alert_email(payload.email, payload.subject, payload.message)

    if not result["success"]:
        raise HTTPException(status_code=502, detail=result["detail"])

    return {
        "status": "success",
        "detail": result["detail"],
    }
