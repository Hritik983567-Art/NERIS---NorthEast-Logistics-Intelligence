from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException, status, Depends
from app.models.telemetry import VehicleTelemetry, TelemetryIngestResponse, ActiveFleetVehicleResponse, SimulatedVehicleState, FleetVehicleItem
from app.services.telemetry_service import get_telemetry_service
from app.core.dependencies import require_roles

router = APIRouter(tags=["Tab 3: Vehicle Tracker & Active Fleet Telemetry"])

@router.post("/fleet/telemetry", response_model=TelemetryIngestResponse, status_code=status.HTTP_200_OK)
@router.post("/api/fleet/telemetry", response_model=TelemetryIngestResponse, status_code=status.HTTP_200_OK)
@router.post("/api/v1/fleet/telemetry", response_model=TelemetryIngestResponse, status_code=status.HTTP_200_OK)
@router.post("/telemetry/ping", response_model=TelemetryIngestResponse, status_code=status.HTTP_200_OK)
@router.post("/api/telemetry/ping", response_model=TelemetryIngestResponse, status_code=status.HTTP_200_OK)
@router.post("/api/v1/telemetry/ping", response_model=TelemetryIngestResponse, status_code=status.HTTP_200_OK)
async def ingest_vehicle_telemetry(
    telemetry: VehicleTelemetry,
    user: Dict[str, Any] = Depends(require_roles(["DISPATCHER", "FIELD_OFFICER", "COMMANDER", "ADMIN"]))
):
    """
    Ingests vehicle telemetry ping, persists item to AWS DynamoDB ('ner_fleet_telemetry'),
    performs real-time Haversine distance proximity calculation against active disaster blockades,
    and returns vehicle status warnings and generated operational alert records.
    Applies resource-level ownership validation for Field Officers.
    """
    user_role = str(user.get("role", "FIELD_OFFICER")).upper()
    username = str(user.get("username", "")).lower()

    # Resource-level rule: FIELD_OFFICER may only ingest telemetry for their own vehicle/driver profile
    if "COMMANDER" not in user_role and "DISPATCHER" not in user_role and "ADMIN" not in user_role:
        driver = str(telemetry.driver_name or "").lower()
        v_id = str(telemetry.vehicle_id or "").lower()
        if driver and username and driver != username and username not in driver and username not in v_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Resource Access Denied: Field Officer '{user.get('username')}' is not authorized to submit telemetry for vehicle '{telemetry.vehicle_id}' driven by '{telemetry.driver_name}'."
            )

    service = get_telemetry_service()
    return service.ingest_telemetry(telemetry)

@router.get("/fleet", response_model=List[ActiveFleetVehicleResponse], status_code=status.HTTP_200_OK)
@router.get("/api/fleet", response_model=List[ActiveFleetVehicleResponse], status_code=status.HTTP_200_OK)
@router.get("/api/v1/fleet", response_model=List[ActiveFleetVehicleResponse], status_code=status.HTTP_200_OK)
@router.get("/api/telemetry/vehicles", response_model=List[ActiveFleetVehicleResponse], status_code=status.HTTP_200_OK)
@router.get("/api/v1/telemetry/active-fleet", response_model=List[ActiveFleetVehicleResponse], status_code=status.HTTP_200_OK)
async def get_all_fleet_vehicles(
    state: Optional[str] = Query(None, description="Filter active fleet by state"),
    user: Dict[str, Any] = Depends(require_roles(["DISPATCHER", "COMMANDER", "ADMIN", "FIELD_OFFICER"]))
):
    """
    Returns all active fleet vehicle states retrieved from backend telemetry engine and DynamoDB.
    """
    service = get_telemetry_service()
    return service.get_all_active_fleets(state=state)

@router.get("/fleet/{vehicle_id}", response_model=FleetVehicleItem, status_code=status.HTTP_200_OK)
@router.get("/api/fleet/{vehicle_id}", response_model=FleetVehicleItem, status_code=status.HTTP_200_OK)
@router.get("/api/v1/fleet/{vehicle_id}", response_model=FleetVehicleItem, status_code=status.HTTP_200_OK)
@router.get("/api/telemetry/vehicles/{vehicle_id}", response_model=FleetVehicleItem, status_code=status.HTTP_200_OK)
async def get_single_fleet_vehicle(
    vehicle_id: str,
    user: Dict[str, Any] = Depends(require_roles(["DISPATCHER", "COMMANDER", "ADMIN", "FIELD_OFFICER"]))
):
    """
    Retrieves vehicle telemetry state for a specific vehicle by ID from backend telemetry store.
    Applies resource-level PII minimization for non-dispatchers.
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
async def get_simulated_telemetry(
    state: Optional[str] = Query(None, description="Filter simulation telemetry by state"),
    user: Dict[str, Any] = Depends(require_roles(["DISPATCHER", "COMMANDER", "ADMIN", "FIELD_OFFICER"]))
):
    """
    Backend simulation endpoint returning exact vehicle state trajectory metadata.
    """
    service = get_telemetry_service()
    return service.get_simulated_telemetry(state=state)
