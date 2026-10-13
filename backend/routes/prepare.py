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
import logging
from datetime import datetime

from ..services import OpenWeatherService
from ..services.decision_support import get_decision_support_service

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
