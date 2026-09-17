from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query, status, HTTPException
from app.services.rainfall_service import get_rainfall_service
from app.models.historical_rainfall import (
    RainfallMetadataResponse,
    RainfallAnalyticsResponse,
    SubdivisionRiskIndex
)

router = APIRouter(prefix="/api/v1/rainfall", tags=["Historical Rainfall Dataset API (1901-2017)"])

@router.get("", status_code=status.HTTP_200_OK)
@router.get("/summary", status_code=status.HTTP_200_OK)
async def get_historical_rainfall_summary():
    """
    Returns summary overview of historical rainfall data across operational North-East subdivisions.
    Includes explicit disclaimer: HISTORICAL RAINFALL — NOT LIVE WEATHER.
    """
    service = get_rainfall_service()
    return service.get_summary()

@router.get("/metadata", response_model=RainfallMetadataResponse, status_code=status.HTTP_200_OK)
async def get_historical_rainfall_metadata():
    """
    Returns official IMD / Kaggle dataset provenance metadata.
    Includes explicit disclaimer: HISTORICAL RAINFALL — NOT LIVE WEATHER.
    """
    service = get_rainfall_service()
    return service.get_metadata()

@router.get("/analytics", response_model=RainfallAnalyticsResponse, status_code=status.HTTP_200_OK)
async def get_historical_rainfall_analytics():
    """
    Returns 117-year historical rainfall analytics (1901-2017):
    - Multi-decade annual rainfall trends
    - Sub-divisional monthly baseline averages
    - Monsoon seasonal breakdown
    - Historical extreme high-rainfall years
    """
    service = get_rainfall_service()
    return service.get_analytics()

@router.get("/trends", status_code=status.HTTP_200_OK)
async def get_historical_rainfall_trends(
    start_year: Optional[int] = Query(None, description="Start year for trend window (1901-2017)"),
    end_year: Optional[int] = Query(None, description="End year for trend window (1901-2017)")
):
    """
    Returns annual rainfall trend series (1901-2017) with optional year range filtering.
    """
    if start_year is not None and (start_year < 1900 or start_year > 2020):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid start_year '{start_year}'. Range must be between 1901 and 2017.")
    if end_year is not None and (end_year < 1900 or end_year > 2020):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid end_year '{end_year}'. Range must be between 1901 and 2017.")
    if start_year is not None and end_year is not None and start_year > end_year:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid year range: start_year ({start_year}) cannot be greater than end_year ({end_year}).")

    service = get_rainfall_service()
    try:
        trends = service.get_trends(start_year=start_year, end_year=end_year)
        return {
            "start_year": start_year or 1901,
            "end_year": end_year or 2017,
            "trend_points": trends,
            "disclaimer": "HISTORICAL RAINFALL — NOT LIVE WEATHER"
        }
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))

@router.get("/subdivisions", status_code=status.HTTP_200_OK)
async def get_subdivision_baselines():
    """
    Returns 117-year monthly means and risk scores for North-East meteorological subdivisions.
    """
    service = get_rainfall_service()
    analytics = service.get_analytics()
    return analytics.get("baselines", {})

@router.get("/risk-index", response_model=List[SubdivisionRiskIndex], status_code=status.HTTP_200_OK)
async def get_monthly_rainfall_risk_index(
    month: Optional[str] = Query("SEP", description="Target month: JAN, FEB, MAR, APR, MAY, JUN, JUL, AUG, SEP, OCT, NOV, DEC")
):
    """
    Returns normalized sub-divisional environmental risk indices for GIS map overlays and route weighting.
    Explicitly labeled: HISTORICAL RAINFALL — NOT LIVE WEATHER.
    """
    service = get_rainfall_service()
    try:
        return service.get_risk_indices_for_month(month=month or "SEP")
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))

@router.get("/{region}", status_code=status.HTTP_200_OK)
async def get_historical_rainfall_by_region(region: str):
    """
    Returns historical rainfall baseline data for a specific subdivision, state, or region code.
    Example regions: 'ASSAM & MEGHALAYA', 'NER_AM', 'Assam', 'Sikkim', 'Arunachal Pradesh'.
    """
    if not region or not region.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Region parameter cannot be empty.")

    service = get_rainfall_service()
    detail = service.get_region_detail(region)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Region '{region}' not found in North-East historical rainfall dataset. Operational scope includes: ASSAM & MEGHALAYA, ARUNACHAL PRADESH, NAGA MANI MIZO TRIPURA, SUB HIMALAYAN WEST BENGAL & SIKKIM."
        )
    return detail

