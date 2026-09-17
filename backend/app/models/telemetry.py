from enum import Enum
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, root_validator
from app.models.routing import CargoType

class FleetVehicleItem(BaseModel):
    vehicleId: str = Field(..., description="Unique vehicle ID, e.g., NER-MED-8041")
    vehicle_id: str = Field(..., description="Alias for vehicleId")
    registration: str = Field("NER-MED-8041", description="Vehicle license registration number")
    vehicleType: str = Field("HEAVY_TRUCK", description="Vehicle category type")
    vehicle_type: str = Field("HEAVY_TRUCK", description="Alias for vehicleType")
    status: str = Field("CLEAR", description="Operational status: CLEAR | CAUTION | BLOCKED | ROUTE AT RISK")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Current GPS Latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Current GPS Longitude")
    lat: float = Field(..., description="Alias for latitude")
    lng: float = Field(..., description="Alias for longitude")
    speed: float = Field(0.0, ge=0.0, description="Speed in km/h")
    speed_kmh: float = Field(0.0, ge=0.0, description="Alias for speed")
    heading: float = Field(0.0, ge=0.0, le=360.0, description="Heading degrees")
    cargo: str = Field("Life-Saving Medical Supplies", description="Cargo payload description")
    cargo_type: str = Field("MEDICINE", description="Cargo category code")
    updatedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), description="ISO 8601 timestamp")
    
    # Extended fields
    driver_name: Optional[str] = Field("Ramesh Kalita", description="Driver full name")
    driver_phone: Optional[str] = Field("+91 98640 11234", description="Driver mobile number")
    state: Optional[str] = Field("assam", description="State region")
    destination: Optional[str] = Field("Silchar Depot", description="Target destination hub")
    route_at_risk: Optional[bool] = Field(False, description="True if hazard threatens current route")
    at_risk_hazard_info: Optional[str] = Field(None, description="Proximity hazard details")
    proximity_alert: Optional[Dict[str, Any]] = Field(None, description="Proximity alert details if within threshold")

    @root_validator(pre=True)
    def resolve_fleet_aliases(cls, values: dict):
        if not values:
            return values
        
        vid = str(values.get("vehicleId") or values.get("vehicle_id") or values.get("id") or "NER-MED-8041")
        reg = str(values.get("registration") or values.get("reg_no") or vid)
        vtype = str(values.get("vehicleType") or values.get("vehicle_type") or "HEAVY_TRUCK")
        stat = str(values.get("status") or "CLEAR").upper()
        
        lat = float(values.get("latitude") if values.get("latitude") is not None else values.get("lat") if values.get("lat") is not None else values.get("current_lat", 26.1445))
        lng = float(values.get("longitude") if values.get("longitude") is not None else values.get("lng") if values.get("lng") is not None else values.get("current_lng", 91.7362))
        
        speed_val = float(values.get("speed") if values.get("speed") is not None else values.get("speed_kmh") if values.get("speed_kmh") is not None else values.get("speedKm", 40.0))
        heading_val = float(values.get("heading") if values.get("heading") is not None else values.get("heading_degrees", 0.0))
        
        cargo_desc = str(values.get("cargo") or values.get("payload") or values.get("category") or "Life-Saving Vaccines & Medical Supplies")
        cargo_code = str(values.get("cargo_type") or values.get("cargoType") or "MEDICINE")
        
        updated_val = str(values.get("updatedAt") or values.get("last_updated") or values.get("timestamp") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        
        values["vehicleId"] = vid
        values["vehicle_id"] = vid
        values["registration"] = reg
        values["vehicleType"] = vtype
        values["vehicle_type"] = vtype
        values["status"] = stat
        values["latitude"] = lat
        values["longitude"] = lng
        values["lat"] = lat
        values["lng"] = lng
        values["speed"] = speed_val
        values["speed_kmh"] = speed_val
        values["heading"] = heading_val
        values["cargo"] = cargo_desc
        values["cargo_type"] = cargo_code
        values["updatedAt"] = updated_val
        return values

class VehicleTelemetry(BaseModel):
    vehicle_id: str = Field(..., description="Unique vehicle ID, e.g., NER-MED-8041")
    vehicleId: Optional[str] = Field(None, description="Alias for vehicle_id")
    registration: Optional[str] = Field("NER-MED-8041", description="Registration number")
    vehicleType: Optional[str] = Field("HEAVY_TRUCK", description="Vehicle type")
    driver_name: Optional[str] = Field("Ramesh Kalita", description="Driver full name")
    driver_phone: Optional[str] = Field("+91 98640 11234", description="Driver mobile contact number")
    current_lat: Optional[float] = Field(None, description="Current GPS Latitude")
    current_lng: Optional[float] = Field(None, description="Current GPS Longitude")
    latitude: Optional[float] = Field(None, description="Latitude")
    longitude: Optional[float] = Field(None, description="Longitude")
    speed_kmh: Optional[float] = Field(40.0, description="Current speed in km/h")
    speed: Optional[float] = Field(None, description="Speed in km/h")
    heading_degrees: Optional[float] = Field(0.0, description="Heading degrees")
    heading: Optional[float] = Field(None, description="Heading degrees")
    cargo: Optional[str] = Field("Life-Saving Medical Supplies", description="Cargo description")
    cargo_type: Optional[str] = Field("MEDICINE", description="Type of cargo being transported")
    destination_district: Optional[str] = Field("Silchar Depot", description="Target destination district or depot")
    timestamp: Optional[str] = Field(None, description="ISO timestamp")

    @root_validator(pre=True)
    def resolve_telemetry_aliases(cls, values: dict):
        if not values:
            return values
        vid = str(values.get("vehicle_id") or values.get("vehicleId") or values.get("id") or "NER-MED-8041")
        lat = float(values.get("current_lat") if values.get("current_lat") is not None else values.get("latitude") if values.get("latitude") is not None else values.get("lat", 26.1445))
        lng = float(values.get("current_lng") if values.get("current_lng") is not None else values.get("longitude") if values.get("longitude") is not None else values.get("lng", 91.7362))
        
        if lat < -90.0 or lat > 90.0:
            raise ValueError(f"Latitude coordinate {lat} is out of bounds (-90 to +90 degrees).")
        if lng < -180.0 or lng > 180.0:
            raise ValueError(f"Longitude coordinate {lng} is out of bounds (-180 to +180 degrees).")

        spd = float(values.get("speed_kmh") if values.get("speed_kmh") is not None else values.get("speed") if values.get("speed") is not None else values.get("speedKm", 40.0))
        hdg = float(values.get("heading_degrees") if values.get("heading_degrees") is not None else values.get("heading", 0.0))
        ts = str(values.get("timestamp") or values.get("updatedAt") or values.get("last_updated") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        
        values["vehicle_id"] = vid
        values["vehicleId"] = vid
        values["current_lat"] = lat
        values["latitude"] = lat
        values["current_lng"] = lng
        values["longitude"] = lng
        values["speed_kmh"] = spd
        values["speed"] = spd
        values["heading_degrees"] = hdg
        values["heading"] = hdg
        values["timestamp"] = ts
        return values

class TelemetryIngestResponse(BaseModel):
    status: str = Field("SUCCESS", description="Ingest status message")
    dynamodb_confirmed: bool = Field(True, description="True if stored in DynamoDB")
    vehicle: FleetVehicleItem = Field(..., description="Persisted vehicle state")
    hazard_in_proximity: bool = Field(False, description="True if vehicle is within proximity threshold")
    proximity_distance_km: Optional[float] = Field(None, description="Calculated distance to nearest active incident in km")
    warning_message: Optional[str] = Field(None, description="Warning message")
    reroute_advised: bool = Field(False, description="True if reroute is advised")
    alert_created: Optional[Dict[str, Any]] = Field(None, description="Operational proximity alert record created")

class SimulatedVehicleState(BaseModel):
    vehicle_id: str = Field(..., description="Vehicle ID registration code")
    latitude: float = Field(..., description="Current latitude coordinate")
    longitude: float = Field(..., description="Current longitude coordinate")
    speed: float = Field(..., description="Current vehicle speed in km/h")
    heading: float = Field(..., description="Compass bearing direction in degrees (0-360)")
    fuel: float = Field(..., description="Fuel level percentage (0-100%)")
    status: str = Field(..., description="Operational status: CLEAR | CAUTION | BLOCKED | ROUTE AT RISK")
    current_route: Dict[str, Any] = Field(default_factory=dict, description="Current predefined route metadata")
    last_updated: str = Field(..., description="ISO 8601 timestamp of last simulation step")
    
    # Extended telemetry attributes for UI backward compatibility
    driver_name: Optional[str] = Field("Ramesh Kalita", description="Driver full name")
    driver_phone: Optional[str] = Field("+91 98640 11234", description="Driver contact number")
    category: Optional[str] = Field("Relief Convoy", description="Payload category description")
    payload: Optional[str] = Field("Life-Saving Medical Supplies", description="Payload details")
    cargo_type: Optional[str] = Field("MEDICINE", description="Cargo type classification")
    cargo_temp_c: Optional[float] = Field(4.5, description="Cargo temperature in °C")
    state: Optional[str] = Field("assam", description="State region location")
    origin: Optional[str] = Field("Guwahati Central Depot", description="Origin hub name")
    destination: Optional[str] = Field("Silchar FCI Hub", description="Destination hub name")
    vehicle_type: Optional[str] = Field("HEAVY_TRUCK", description="Vehicle transport type")
    route_at_risk: bool = Field(False, description="True if high-severity hazard threatens current route")
    at_risk_hazard_info: Optional[str] = Field(None, description="Hazard description if route is at risk")

class ActiveFleetVehicleResponse(BaseModel):
    id: str = Field(..., description="Vehicle registration ID")
    driver: str = Field(..., description="Driver name")
    category: str = Field(..., description="Payload type description")
    payload: str = Field(..., description="Payload details")
    state: str = Field(..., description="Current state location")
    currentLocationName: str = Field(..., description="Human readable location name")
    lat: float = Field(..., description="Latitude")
    lng: float = Field(..., description="Longitude")
    speedKm: float = Field(..., description="Speed in km/h")
    cargoTempC: float = Field(..., description="Temperature in °C")
    eta: str = Field(..., description="Estimated arrival time")
    status: str = Field(..., description="Status: CLEAR | CAUTION | BLOCKED | ROUTE AT RISK")
    heading: Optional[float] = Field(0.0, description="Heading degrees")
    fuelPercent: Optional[float] = Field(80.0, description="Fuel level percent")
    route_at_risk: Optional[bool] = Field(False, description="True if route is at risk")
    at_risk_hazard_info: Optional[str] = Field(None, description="Hazard details")
