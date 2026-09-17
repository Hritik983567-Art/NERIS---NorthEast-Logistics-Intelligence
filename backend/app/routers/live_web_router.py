from typing import List, Optional
from fastapi import APIRouter, Query, status
from app.models.live_web import LiveNewsResponse, LiveWeatherResponse, LiveIncidentAlert
from app.services.live_web_service import get_live_web_service
from app.services.weather_service import get_weather_service

router = APIRouter(prefix="/api/v1/live", tags=["Real-Time Web Intelligence & Weather"])

@router.get("/news", response_model=LiveNewsResponse, status_code=status.HTTP_200_OK)
async def get_live_web_news(
    state: Optional[str] = Query(None, description="Filter live web news by NER state"),
    refresh: bool = Query(False, description="Force instant live web re-crawl of RSS feeds")
):
    """
    Fetches real live news articles, disaster alerts, and BRO advisories parsed from Google News RSS feeds for North-East India.
    """
    service = get_live_web_service()
    return service.fetch_live_news(state_filter=state, force_refresh=refresh)

@router.get("/weather", response_model=LiveWeatherResponse, status_code=status.HTTP_200_OK)
async def get_live_web_weather(
    refresh: bool = Query(False, description="Force instant re-fetch from Open-Meteo REST API")
):
    """
    Fetches real-time temperature, rainfall, wind speeds, and risk categories for North-East hubs via Open-Meteo REST API.
    """
    service = get_weather_service()
    return service.fetch_live_weather_batch(force_refresh=refresh)

@router.get("/incidents", response_model=List[LiveIncidentAlert], status_code=status.HTTP_200_OK)
async def get_live_web_incidents():
    """
    Returns real live road hazard alerts and weather blockades dynamically synthesized from real web sources.
    """
    service = get_live_web_service()
    return service.fetch_live_incidents()
