from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException, status
from app.services.landslide_flood_service import get_landslide_flood_service
from app.models.historical_landslide_flood import (
    HistoricalLandslideFloodMetadata,
    HistoricalEventRecord,
    LandslideFloodAnalyticsResponse,
    EnvironmentalRiskIndexResponse,
    EnvironmentalRiskSummaryResponse,
    EnvironmentalRiskRegionDetailResponse,
    EnvironmentalRiskTrendsResponse
)

router = APIRouter(tags=["Historical Flood & Landslide Risk Intelligence (2000-2023)"])

# Primary Prefix: /api/v1/environmental-risk
@router.get("/api/v1/environmental-risk/summary", response_model=EnvironmentalRiskSummaryResponse, status_code=status.HTTP_200_OK)
async def get_environmental_risk_summary():
    """
    Returns historical environmental risk summary across all 8 North-Eastern states.
    Strictly tagged with data_type = 'historical' and source_type = 'historical_dataset'.
    """
    service = get_landslide_flood_service()
    return service.get_summary()

@router.get("/api/v1/environmental-risk/index", response_model=List[EnvironmentalRiskIndexResponse], status_code=status.HTTP_200_OK)
async def get_environmental_risk_indices(
    state: Optional[str] = Query(None, description="Optional state name to filter risk index")
):
    """
    Returns 0-100 environmental risk index for North-Eastern states.
    """
    service = get_landslide_flood_service()
    results = service.get_risk_indices(state=state)
    if state and not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"State '{state}' not recognized within North-East operational scope."
        )
    return results

@router.get("/api/v1/environmental-risk/region/{state}", response_model=EnvironmentalRiskRegionDetailResponse, status_code=status.HTTP_200_OK)
async def get_environmental_risk_region_detail(state: str):
    """
    Returns detailed environmental risk breakdown and historical event records for a specific state.
    Returns 404 HTTP status code if state is invalid or outside North-East scope.
    """
    if not state or not state.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State parameter cannot be empty."
        )

    service = get_landslide_flood_service()
    detail = service.get_region_detail(state=state)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Region/State '{state}' not found in historical flood & landslide dataset."
        )
    return detail

@router.get("/api/v1/environmental-risk/trends", response_model=EnvironmentalRiskTrendsResponse, status_code=status.HTTP_200_OK)
async def get_environmental_risk_trends(
    start_year: Optional[int] = Query(None, description="Filter start year (2000-2023)"),
    end_year: Optional[int] = Query(None, description="Filter end year (2000-2023)")
):
    """
    Returns historical temporal trends (yearly and monthly distribution) for environmental disaster events.
    Validates that start_year <= end_year and within valid range.
    """
    if start_year is not None and end_year is not None:
        if start_year > end_year:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid year range: start_year ({start_year}) cannot be greater than end_year ({end_year})."
            )

    if start_year is not None and (start_year < 1900 or start_year > 2100):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid start_year ({start_year}). Must be between 1900 and 2100."
        )

    if end_year is not None and (end_year < 1900 or end_year > 2100):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid end_year ({end_year}). Must be between 1900 and 2100."
        )

    service = get_landslide_flood_service()
    return service.get_trends(start_year=start_year, end_year=end_year)

@router.get("/api/v1/environmental-risk/records", response_model=List[HistoricalEventRecord], status_code=status.HTTP_200_OK)
async def get_environmental_risk_records(
    event_type: Optional[str] = Query(None, description="Filter by event type: LANDSLIDE | FLOOD"),
    state: Optional[str] = Query(None, description="Filter by state name")
):
    """
    Returns historical event records for research analysis and GIS map rendering.
    Every record is strictly tagged with source_type = 'historical_dataset' and data_type = 'historical'.
    """
    service = get_landslide_flood_service()
    return service.get_historical_records(event_type=event_type, state=state)

@router.get("/api/v1/environmental-risk/metadata", response_model=HistoricalLandslideFloodMetadata, status_code=status.HTTP_200_OK)
async def get_environmental_risk_metadata():
    """
    Returns dataset metadata and provenance notice for Kaggle Landslide & Flood dataset.
    """
    service = get_landslide_flood_service()
    return service.get_metadata()


# Legacy & Alias Routes under /api/v1/historical-events for backward compatibility
@router.get("/api/v1/historical-events/metadata", response_model=HistoricalLandslideFloodMetadata, status_code=status.HTTP_200_OK)
async def get_historical_events_metadata_alias():
    service = get_landslide_flood_service()
    return service.get_metadata()

@router.get("/api/v1/historical-events/analytics", response_model=EnvironmentalRiskSummaryResponse, status_code=status.HTTP_200_OK)
async def get_historical_events_analytics_alias():
    service = get_landslide_flood_service()
    return service.get_summary()

@router.get("/api/v1/historical-events/records", response_model=List[HistoricalEventRecord], status_code=status.HTTP_200_OK)
async def get_historical_event_records_alias(
    event_type: Optional[str] = Query(None),
    state: Optional[str] = Query(None)
):
    service = get_landslide_flood_service()
    return service.get_historical_records(event_type=event_type, state=state)

@router.get("/api/v1/historical-events/risk-overlay", status_code=status.HTTP_200_OK)
async def get_historical_risk_overlay_alias():
    service = get_landslide_flood_service()
    analytics = service.get_analytics()
    return {
        "state_landslide_exposure": analytics.get("state_landslide_exposure", {}),
        "state_flood_exposure": analytics.get("state_flood_exposure", {}),
        "disclaimer": "HISTORICAL DATASET EVENT (source_type = 'historical_dataset') — NOT LIVE VERIFIED INCIDENT"
    }
