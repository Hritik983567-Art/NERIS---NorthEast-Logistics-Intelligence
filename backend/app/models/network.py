from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class NetworkNodeModel(BaseModel):
    id: str = Field(..., description="Unique node identifier, e.g., Guwahati")
    lat: float = Field(..., description="GPS Latitude")
    lng: float = Field(..., description="GPS Longitude")
    elevation_m: int = Field(..., description="Elevation in meters above sea level")
    state: str = Field(..., description="State name, e.g., Assam")
    district: Optional[str] = Field(None, description="District name")
    type: str = Field(..., description="Node category, e.g., STATE_CAPITAL, PRIMARY_DEPOT")

class NetworkEdgeModel(BaseModel):
    from_node: str = Field(..., description="Origin node ID")
    to_node: str = Field(..., description="Destination node ID")
    length_km: float = Field(..., description="Distance in kilometers")
    highway_name: str = Field(..., description="Highway ID, e.g., NH-40")
    elevation_profile: str = Field(..., description="Terrain profile, e.g., STEEP_GHAT")
    vulnerability_index: float = Field(..., ge=0.0, le=1.0, description="Vulnerability score from 0.0 to 1.0")
    max_weight_tons: float = Field(..., description="Maximum bridge load limit in metric tonnes")
    base_speed_kmh: float = Field(..., description="Base vehicle speed in km/h")

class NetworkOverviewResponse(BaseModel):
    total_nodes: int = Field(..., description="Total count of active transportation hubs")
    total_edges: int = Field(..., description="Total count of connecting highway corridors")
    states_covered: List[str] = Field(..., description="List of NER states integrated")
    high_vulnerability_corridors: int = Field(..., description="Count of edges with vulnerability index > 0.70")
    average_elevation_m: float = Field(..., description="Average node elevation across graph")

class CorridorStatusModel(BaseModel):
    id: str = Field(..., description="Corridor highway identifier e.g. NH-27")
    name: str = Field(..., description="Corridor name e.g. Guwahati - Siliguri Transit Corridor")
    route: str = Field(..., description="Route segment nodes")
    state: str = Field(..., description="Primary state location")
    status: str = Field("clear", description="Corridor accessibility status: clear | caution | blocked")
    active_incidents_count: int = Field(0, description="Number of active DynamoDB incident hazards affecting this corridor")
    vulnerability_index: float = Field(0.3, description="Hazard vulnerability index")
    length_km: float = Field(..., description="Corridor length in km")
    max_weight_tons: float = Field(30.0, description="Bridge weight capacity limit in metric tonnes")

