from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, status
from app.models.telemetry import VehicleTelemetry, TelemetryIngestResponse, ActiveFleetVehicleResponse, SimulatedVehicleState, FleetVehicleItem
from app.services.telemetry_service import get_telemetry_service

router = APIRouter(tags=["Tab 3: Vehicle Tracker & Active Fleet Telemetry"])

@router.post("/fleet/telemetry", response_model=TelemetryIngestResponse, status_code=status.HTTP_200_OK)
@router.post("/api/fleet/telemetry", response_model=TelemetryIngestResponse, status_code=status.HTTP_200_OK)
@router.post("/api/v1/fleet/telemetry", response_model=TelemetryIngestResponse, status_code=status.HTTP_200_OK)
@router.post("/telemetry/ping", response_model=TelemetryIngestResponse, status_code=status.HTTP_200_OK)
@router.post("/api/telemetry/ping", response_model=TelemetryIngestResponse, status_code=status.HTTP_200_OK)
@router.post("/api/v1/telemetry/ping", response_model=TelemetryIngestResponse, status_code=status.HTTP_200_OK)
async def ingest_vehicle_telemetry(telemetry: VehicleTelemetry):
    """
    Ingests vehicle telemetry ping, persists item to AWS DynamoDB ('ner_fleet_telemetry'),
    performs real-time Haversine distance proximity calculation against active disaster blockades,
    and returns vehicle status warnings and generated operational alert records.
    """
    service = get_telemetry_service()
    return service.ingest_telemetry(telemetry)

@router.get("/fleet", response_model=List[ActiveFleetVehicleResponse], status_code=status.HTTP_200_OK)
@router.get("/api/fleet", response_model=List[ActiveFleetVehicleResponse], status_code=status.HTTP_200_OK)
@router.get("/api/v1/fleet", response_model=List[ActiveFleetVehicleResponse], status_code=status.HTTP_200_OK)
@router.get("/api/telemetry/vehicles", response_model=List[ActiveFleetVehicleResponse], status_code=status.HTTP_200_OK)
@router.get("/api/v1/telemetry/active-fleet", response_model=List[ActiveFleetVehicleResponse], status_code=status.HTTP_200_OK)
async def get_all_fleet_vehicles(state: Optional[str] = Query(None, description="Filter active fleet by state")):
    """
    Returns all active fleet vehicle states retrieved from backend telemetry engine and DynamoDB.
    """
    service = get_telemetry_service()
    return service.get_all_active_fleets(state=state)

@router.get("/fleet/{vehicle_id}", response_model=FleetVehicleItem, status_code=status.HTTP_200_OK)
@router.get("/api/fleet/{vehicle_id}", response_model=FleetVehicleItem, status_code=status.HTTP_200_OK)
@router.get("/api/v1/fleet/{vehicle_id}", response_model=FleetVehicleItem, status_code=status.HTTP_200_OK)
@router.get("/api/telemetry/vehicles/{vehicle_id}", response_model=FleetVehicleItem, status_code=status.HTTP_200_OK)
async def get_single_fleet_vehicle(vehicle_id: str):
    """
    Retrieves vehicle telemetry state for a specific vehicle by ID from backend telemetry store.
    """
    service = get_telemetry_service()
    vehicle = service.get_vehicle_by_id(vehicle_id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle '{vehicle_id}' not found."
        )
    return vehicle

@router.get("/api/v1/telemetry/simulation", response_model=List[SimulatedVehicleState], status_code=status.HTTP_200_OK)
async def get_simulated_telemetry(state: Optional[str] = Query(None, description="Filter simulation telemetry by state")):
    """
    Backend simulation endpoint returning exact vehicle state trajectory metadata.
    """
    service = get_telemetry_service()
    return service.get_simulated_telemetry(state=state)
