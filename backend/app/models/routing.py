from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, root_validator

class CargoType(str, Enum):
    MEDICINE = "MEDICINE"
    OXYGEN_CYLINDERS = "OXYGEN_CYLINDERS"
    GRAINS_RATIONS = "GRAINS_RATIONS"
    FUEL = "FUEL"
    CONSTRUCTION = "CONSTRUCTION"
    GENERAL = "GENERAL"

class OptimizeRouteRequest(BaseModel):
    origin: str = Field("Guwahati", description="Origin hub or location name, e.g., Guwahati")
    destination: str = Field("Silchar", description="Destination hub or location name, e.g., Silchar")
    origin_node: str = Field("Guwahati", description="Legacy field for origin node")
    destination_node: str = Field("Silchar", description="Legacy field for destination node")
    vehicleType: Optional[str] = Field("HEAVY_CONVOY", description="Vehicle type, e.g., HEAVY_CONVOY, AMBULANCE, TANKER")
    cargoType: Optional[CargoType] = Field(CargoType.MEDICINE, description="Type of cargo being transported")
    cargo_type: Optional[CargoType] = Field(CargoType.MEDICINE, description="Legacy field for cargo type")
    convoy_weight_tons: float = Field(15.0, ge=1.0, le=70.0, description="Gross convoy weight in metric tonnes")
    weather_condition: str = Field("MONSOON_STORM", description="Weather condition: CLEAR | HEAVY_RAIN | MONSOON_STORM")
    constraints: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional routing constraints")

    @root_validator(pre=True)
    def resolve_aliases(cls, values: dict):
        if not values:
            return values
        o = values.get("origin") or values.get("origin_node") or "Guwahati"
        d = values.get("destination") or values.get("destination_node") or "Silchar"
        c = values.get("cargoType") or values.get("cargo_type") or "MEDICINE"
        values["origin"] = o
        values["origin_node"] = o
        values["destination"] = d
        values["destination_node"] = d
        values["cargoType"] = c
        values["cargo_type"] = c
        return values

class RouteSegment(BaseModel):
    from_node: str = Field(..., description="Segment starting node")
    to_node: str = Field(..., description="Segment ending node")
    distance_km: float = Field(..., ge=0.0, description="Segment distance in kilometers")
    terrain_type: str = Field(..., description="Terrain profile: VALLEY | STEEP_GHAT | PLAINS | MODERATE_HILL | EXTREME_SLOPE")
    standard_time_hours: float = Field(..., ge=0.0, description="Standard travel time without hazards")
    adjusted_time_hours: float = Field(..., ge=0.0, description="Disaster & weather adjusted travel time")
    active_incident_ids: List[str] = Field(default_factory=list, description="IDs of active incidents on this segment")
    risk_factor: float = Field(..., ge=0.0, le=1.0, description="Segment vulnerability risk score")

class RouteDetail(BaseModel):
    routeId: str = Field(..., description="Route ID")
    route_name: str = Field(..., description="Descriptive route name")
    geometry: List[List[float]] = Field(..., description="List of [latitude, longitude] coordinates")
    distance: float = Field(..., ge=0.0, description="Distance in km")
    duration: float = Field(..., ge=0.0, description="Duration in hours")
    riskScore: float = Field(..., ge=0.0, le=100.0, description="Deterministic risk score out of 100")
    riskLevel: str = Field(..., description="Risk level: LOW | MODERATE | HIGH | CRITICAL")
    riskFactors: List[str] = Field(default_factory=list, description="List of risk factors")
    recommended: bool = Field(True, description="Whether this is the recommended route")
    path_nodes: List[str] = Field(default_factory=list, description="Sequential list of node names")
    rationale: str = Field("", description="Operational rationale")

class OptimizedRouteResponse(BaseModel):
    routeId: str = Field(..., description="Unique generated route ID")
    route_id: str = Field(..., description="Alias for routeId")
    origin: str = Field(..., description="Origin node name")
    destination: str = Field(..., description="Destination node name")
    geometry: List[List[float]] = Field(..., description="Polyline GPS coordinates [[lat, lng], ...]")
    path_nodes: List[str] = Field(..., description="Sequential list of node names in route path")
    
    distance: float = Field(..., ge=0.0, description="Total primary route distance in kilometers")
    duration: float = Field(..., ge=0.0, description="Estimated time in hours")
    estimated_time: float = Field(..., ge=0.0, description="Alias for duration")
    riskScore: float = Field(..., ge=0.0, le=100.0, description="Route risk index score out of 100")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Alias for riskScore")
    riskLevel: str = Field(..., description="Risk level: LOW | MODERATE | HIGH | CRITICAL")
    risk_level: str = Field(..., description="Alias for riskLevel")
    riskFactors: List[str] = Field(default_factory=list, description="List of identified operational risk factors")
    risk_factors: List[str] = Field(default_factory=list, description="Alias for riskFactors")
    recommended: bool = Field(True, description="True for primary route")
    
    blocked_segments: List[str] = Field(default_factory=list, description="List of impassable or high-hazard highway corridors")
    alternate_route: Optional[Dict[str, Any]] = Field(None, description="Secondary fallback route details")
    decision_explanation: str = Field(..., description="Detailed operational rationale for primary route selection over alternates")
    bedrock_explanation: Optional[str] = Field(None, description="Optional Bedrock natural-language explanation")
    data_source_mode: str = Field("NERIS_GRAPH_OSRM", description="Dataset provenance label")
    
    # Legacy fields for backward compatibility
    total_distance_km: float = Field(..., ge=0.0, description="Total path distance in kilometers")
    normal_eta_hours: float = Field(..., ge=0.0, description="Normal travel ETA in hours")
    disaster_adjusted_eta_hours: float = Field(..., ge=0.0, description="Disaster & terrain adjusted ETA in hours")
    net_delay_hours: float = Field(..., ge=0.0, description="Calculated net delay in hours")
    safety_score: float = Field(..., ge=0.0, le=100.0, description="Cumulative route safety score out of 100.0")
    turn_by_turn: List[RouteSegment] = Field(default_factory=list, description="List of turn-by-turn route segments")
    alternate_paths: List[Dict[str, Any]] = Field(default_factory=list, description="Secondary fallback route list")
