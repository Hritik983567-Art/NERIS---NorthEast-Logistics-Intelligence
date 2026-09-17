from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException, status
from app.services.emergency_resource_service import get_emergency_resource_service
from app.models.emergency_resource import (
    EmergencyResourceMetadata,
    EmergencyResourceRecord,
    EmergencyResourceSummaryResponse,
    EmergencyResourceCoverageResponse,
    EmergencyResourceRegionDetailResponse,
    EmergencyResourceTrendsResponse
)

router = APIRouter(prefix="/api/v1/emergency-resources", tags=["Historical Emergency Resource Allocation Intelligence API (Dataset 4)"])

@router.get("/summary", response_model=EmergencyResourceSummaryResponse, status_code=status.HTTP_200_OK)
async def get_emergency_resource_summary():
    """
    Returns historical emergency resource allocation summary across all 8 North-Eastern states.
    Strictly tagged with data_type = 'historical' and source_type = 'historical_dataset'.
    """
    service = get_emergency_resource_service()
    return service.get_summary()

@router.get("/types", status_code=status.HTTP_200_OK)
async def get_emergency_resource_types():
    """
    Returns normalized emergency resource categories (HOSPITAL, WAREHOUSE, SHELTER, TRANSPORT).
    """
    service = get_emergency_resource_service()
    return service.get_types()

@router.get("/coverage", response_model=List[EmergencyResourceCoverageResponse], status_code=status.HTTP_200_OK)
async def get_emergency_resource_coverage(
    state: Optional[str] = Query(None, description="Optional state name to filter resource coverage")
):
    """
    Returns 0-100 historical resource coverage score for North-Eastern states.
    """
    service = get_emergency_resource_service()
    results = service.get_coverage(state=state)
    if state and not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"State '{state}' not recognized within North-East operational scope."
        )
    return results

@router.get("/region/{state}", response_model=EmergencyResourceRegionDetailResponse, status_code=status.HTTP_200_OK)
async def get_emergency_resource_region_detail(state: str):
    """
    Returns detailed historical emergency resource allocation breakdown for a specific state.
    Returns 404 HTTP status code if state is invalid or outside North-East scope.
    """
    if not state or not state.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State parameter cannot be empty."
        )

    service = get_emergency_resource_service()
    detail = service.get_region_detail(state=state)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Region/State '{state}' not found in historical emergency resources dataset."
        )
    return detail

@router.get("/trends", response_model=EmergencyResourceTrendsResponse, status_code=status.HTTP_200_OK)
async def get_emergency_resource_trends(
    start_year: Optional[int] = Query(None, description="Filter start year (2022-2026)"),
    end_year: Optional[int] = Query(None, description="Filter end year (2022-2026)")
):
    """
    Returns temporal baseline distribution for historical emergency resources.
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

    service = get_emergency_resource_service()
    return service.get_trends(start_year=start_year, end_year=end_year)

@router.get("/analytics", response_model=EmergencyResourceSummaryResponse, status_code=status.HTTP_200_OK)
async def get_emergency_resource_analytics():
    """
    Returns resource allocation analytics breakdown for Analytics Dashboard.
    """
    service = get_emergency_resource_service()
    return service.get_summary()

@router.get("/metadata", response_model=EmergencyResourceMetadata, status_code=status.HTTP_200_OK)
async def get_emergency_resource_metadata():
    """
    Returns dataset metadata and provenance notice for Kaggle Emergency Resource Allocation Intelligence Data.
    """
    service = get_emergency_resource_service()
    return service.get_metadata()

@router.get("/resources", response_model=List[EmergencyResourceRecord], status_code=status.HTTP_200_OK)
async def get_emergency_resources(
    type: Optional[str] = Query(None, description="Filter by resource type: HOSPITAL | WAREHOUSE | SHELTER | TRANSPORT"),
    state: Optional[str] = Query(None, description="Filter by state name")
):
    """
    Returns list of historical emergency resource records.
    Every record is strictly tagged with source_type = 'historical_dataset' and data_type = 'historical'.
    """
    service = get_emergency_resource_service()
    return service.get_resources(resource_type=type, state=state)

@router.get("/{resource_id}", response_model=EmergencyResourceRecord, status_code=status.HTTP_200_OK)
async def get_emergency_resource_by_id(resource_id: str):
    """
    Returns detailed information for a specific historical emergency resource record by ID.
    Returns 404 HTTP status code if resource_id is not found.
    """
    service = get_emergency_resource_service()
    res = service.get_resource_by_id(resource_id=resource_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emergency resource record '{resource_id}' not found in Dataset 4 database."
        )
    return res
