from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query, status, HTTPException
from app.services.road_accident_service import get_road_accident_service
from app.models.historical_road_accident import (
    RoadAccidentMetadataResponse,
    RoadAccidentAnalyticsResponse,
    RoadRiskIndex
)

router = APIRouter(prefix="/api/v1/road-risk", tags=["Historical Road Accident Dataset API (2022-2025)"])

@router.get("", status_code=status.HTTP_200_OK)
@router.get("/summary", status_code=status.HTTP_200_OK)
async def get_historical_road_risk_summary():
    """
    Returns summary overview of historical road accident statistical data across operational North-East states.
    Includes explicit disclaimer: HISTORICAL ACCIDENT RISK — NOT LIVE INCIDENTS.
    """
    service = get_road_accident_service()
    return service.get_summary()

@router.get("/metadata", response_model=RoadAccidentMetadataResponse, status_code=status.HTTP_200_OK)
async def get_historical_road_risk_metadata():
    """
    Returns official Kaggle Indian Road Accident Dataset 2022-2025 provenance metadata.
    Includes explicit disclaimer: HISTORICAL ACCIDENT RISK — NOT LIVE INCIDENTS.
    """
    service = get_road_accident_service()
    return service.get_metadata()

@router.get("/analytics", response_model=RoadAccidentAnalyticsResponse, status_code=status.HTTP_200_OK)
async def get_historical_road_risk_analytics():
    """
    Returns aggregated historical road risk analytics (2022-2025):
    - State risk baselines and rankings
    - Multi-year accident trends (2022-2025)
    - High-risk contributing factor breakdowns (Weather, Severity, Visibility, Traffic)
    - Normalized state road risk indices
    """
    service = get_road_accident_service()
    return service.get_analytics()

@router.get("/trends", status_code=status.HTTP_200_OK)
async def get_historical_road_risk_trends(
    start_year: Optional[int] = Query(None, description="Start year for trend window (2022-2025)"),
    end_year: Optional[int] = Query(None, description="End year for trend window (2022-2025)")
):
    """
    Returns annual road accident statistical trend series (2022-2025) with optional year range filtering.
    """
    if start_year is not None and (start_year < 2020 or start_year > 2030):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid start_year '{start_year}'. Range must be between 2022 and 2025.")
    if end_year is not None and (end_year < 2020 or end_year > 2030):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid end_year '{end_year}'. Range must be between 2022 and 2025.")
    if start_year is not None and end_year is not None and start_year > end_year:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid year range: start_year ({start_year}) cannot be greater than end_year ({end_year}).")

    service = get_road_accident_service()
    try:
        trends = service.get_trends(start_year=start_year, end_year=end_year)
        return {
            "start_year": start_year or 2022,
            "end_year": end_year or 2025,
            "trend_points": trends,
            "disclaimer": "HISTORICAL ACCIDENT RISK — NOT LIVE INCIDENTS"
        }
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))

@router.get("/risk-index", response_model=List[RoadRiskIndex], status_code=status.HTTP_200_OK)
async def get_road_risk_index():
    """
    Returns normalized state road risk indices for GIS map overlays and route weighting.
    Explicitly labeled: HISTORICAL ACCIDENT RISK — NOT LIVE INCIDENTS.
    """
    service = get_road_accident_service()
    analytics = service.get_analytics()
    return analytics.get("risk_indices", [])

@router.get("/{region}", status_code=status.HTTP_200_OK)
async def get_historical_road_risk_by_region(region: str):
    """
    Returns historical road accident statistical baseline data for a specific North-East state.
    Example regions: 'Assam', 'Meghalaya', 'Arunachal Pradesh', 'Nagaland', 'Manipur', 'Mizoram', 'Tripura', 'Sikkim'.
    """
    if not region or not region.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Region parameter cannot be empty.")

    service = get_road_accident_service()
    detail = service.get_region_detail(region)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"State '{region}' not found in North-East historical road accident dataset. Operational scope includes: Assam, Meghalaya, Arunachal Pradesh, Nagaland, Manipur, Mizoram, Tripura, Sikkim."
        )
    return detail
