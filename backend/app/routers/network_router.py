from typing import List, Optional
from fastapi import APIRouter, Query, status
from app.models.network import NetworkNodeModel, NetworkEdgeModel, NetworkOverviewResponse, CorridorStatusModel
from app.services.network_service import get_network_service

router = APIRouter(prefix="/api/v1/network", tags=["Tab 1: GIS Map & Infrastructure Network"])

@router.get("/nodes", response_model=List[NetworkNodeModel], status_code=status.HTTP_200_OK)
async def get_network_nodes(state: Optional[str] = Query(None, description="Filter hubs by state name")):
    """
    Returns strategic logistics hubs across the 8 NER states with GPS coordinates, elevation, state, and hub category.
    """
    service = get_network_service()
    return service.get_all_nodes(state=state)

@router.get("/edges", response_model=List[NetworkEdgeModel], status_code=status.HTTP_200_OK)
async def get_network_edges():
    """
    Returns highway edge corridors with distance km, highway name, elevation profile, vulnerability index, and bridge load limits.
    """
    service = get_network_service()
    return service.get_all_edges()

@router.get("/corridors", response_model=List[CorridorStatusModel], status_code=status.HTTP_200_OK)
async def get_network_corridors(state: Optional[str] = Query(None, description="Filter corridors by state name")):
    """
    Returns dynamic highway corridor status evaluated against active DynamoDB incident hazards.
    """
    service = get_network_service()
    return service.get_corridor_statuses(state_filter=state)

@router.get("/overview", response_model=NetworkOverviewResponse, status_code=status.HTTP_200_OK)
async def get_network_overview():
    """
    Returns summary statistics for the transportation network graph across all NER states.
    """
    service = get_network_service()
    return service.get_overview()

