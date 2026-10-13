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
