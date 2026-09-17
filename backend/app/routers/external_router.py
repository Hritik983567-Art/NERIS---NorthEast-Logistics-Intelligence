from typing import Optional
from fastapi import APIRouter, Query, status
from app.models.external_record import ExternalDataResponse, AdapterFetchResult, RecordCategory
from app.services.external_data_service import get_external_data_manager

router = APIRouter(prefix="/api/v1/external", tags=["NERIS External Data Integration Layer & Provider Adapters"])

@router.get("/news", response_model=AdapterFetchResult, status_code=status.HTTP_200_OK)
async def get_external_news(
    state: Optional[str] = Query(None, description="Filter news by state"),
    refresh: bool = Query(False, description="Force provider cache refresh")
):
    """
    Fetches external news records via GoogleNewsRSSAdapter.
    Returns standard records with source, source_url, retrieved_at, published_at, title, and content_summary.
    If provider API is unreachable, returns is_available=false without generating fake data.
    """
    manager = get_external_data_manager()
    return await manager.fetch_category_records(RecordCategory.NEWS, state_filter=state, force_refresh=refresh)

@router.get("/weather", response_model=AdapterFetchResult, status_code=status.HTTP_200_OK)
async def get_external_weather(
    state: Optional[str] = Query(None, description="Filter weather by state"),
    refresh: bool = Query(False, description="Force provider cache refresh")
):
    """
    Fetches live weather records for NER hubs via OpenMeteoWeatherAdapter.
    """
    manager = get_external_data_manager()
    return await manager.fetch_category_records(RecordCategory.WEATHER, state_filter=state, force_refresh=refresh)

@router.get("/disasters", response_model=AdapterFetchResult, status_code=status.HTTP_200_OK)
async def get_external_disasters(
    state: Optional[str] = Query(None, description="Filter disaster alerts by state"),
    refresh: bool = Query(False, description="Force provider cache refresh")
):
    """
    Fetches live disaster advisories via DisasterFeedAdapter.
    """
    manager = get_external_data_manager()
    return await manager.fetch_category_records(RecordCategory.DISASTER, state_filter=state, force_refresh=refresh)

@router.get("/govt-notices", response_model=AdapterFetchResult, status_code=status.HTTP_200_OK)
async def get_external_govt_notices(
    state: Optional[str] = Query(None, description="Filter govt notices by state"),
    refresh: bool = Query(False, description="Force provider cache refresh")
):
    """
    Fetches live BRO / PWD / NHIDCL infrastructure notices via BROGovInfraAdapter.
    """
    manager = get_external_data_manager()
    return await manager.fetch_category_records(RecordCategory.GOVT_NOTICE, state_filter=state, force_refresh=refresh)

@router.get("/road-conditions", response_model=AdapterFetchResult, status_code=status.HTTP_200_OK)
async def get_external_road_conditions(
    state: Optional[str] = Query(None, description="Filter road corridors by state"),
    refresh: bool = Query(False, description="Force provider cache refresh")
):
    """
    Fetches dynamic highway corridor accessibility records via RoadConditionAdapter.
    """
    manager = get_external_data_manager()
    return await manager.fetch_category_records(RecordCategory.ROAD_CONDITION, state_filter=state, force_refresh=refresh)

@router.get("/all-records", response_model=ExternalDataResponse, status_code=status.HTTP_200_OK)
async def get_all_external_records(
    state: Optional[str] = Query(None, description="Filter all records by state"),
    refresh: bool = Query(False, description="Force cache refresh across all adapters")
):
    """
    Aggregates all external data records across News, Weather, Disasters, Govt Notices, and Road Conditions.
    """
    manager = get_external_data_manager()
    return await manager.fetch_all_external_records(state_filter=state, force_refresh=refresh)
