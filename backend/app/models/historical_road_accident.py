from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class RoadAccidentMetadataResponse(BaseModel):
    dataset_name: str = Field(..., description="Dataset name")
    source_organization: str = Field(..., description="Source organization (Kaggle)")
    kaggle_source_url: str = Field(..., description="Kaggle dataset URL")
    license: str = Field("CC0: Public Domain / Open Research Dataset", description="Open dataset license")
    retrieval_date: str = Field(..., description="Retrieval date")
    coverage_period: str = Field("2022–2025", description="Coverage period")
    source_type: str = Field("historical_synthetic_dataset", description="Source data type")
    neris_operational_scope: List[str] = Field(default_factory=list, description="North East India states")
    synthetic_data_limitations: str = Field(..., description="Synthetic coordinate disclaimer")
    preprocessing_steps: List[str] = Field(default_factory=list, description="Preprocessing steps")
    fields_used: List[str] = Field(default_factory=list, description="Fields used for aggregation")
    fields_ignored: List[str] = Field(default_factory=list, description="Fields ignored for direct map pins")
    disclaimer: str = Field("HISTORICAL ROAD RISK — NOT LIVE ACCIDENT DATA", description="Mandatory historical disclaimer")
    status: str = Field("VALIDATED_AND_AGGREGATED", description="Ingestion validation status")

class StateRoadRiskStats(BaseModel):
    state: str = Field(..., description="State name")
    total_accidents: int = Field(..., description="Total historical accident count (2022-2025)")
    fatal_accidents: int = Field(..., description="Fatal accident count")
    severe_injuries: int = Field(..., description="Severe injury count")
    total_casualties: int = Field(..., description="Total casualty count")
    average_event_risk_score: float = Field(..., description="Calculated average historical road risk score")
    risk_level: str = Field(..., description="Risk category: LOW | MODERATE | HIGH | CRITICAL")
    route_risk_multiplier: float = Field(..., description="Deterministic Dijkstra multiplier factor (1.0x to 1.35x)")
    severity_breakdown: Dict[str, int] = Field(default_factory=dict, description="Accident count by severity")
    road_type_breakdown: Dict[str, int] = Field(default_factory=dict, description="Accident count by road type")
    weather_breakdown: Dict[str, int] = Field(default_factory=dict, description="Accident count by weather condition")
    time_of_day_breakdown: Dict[str, int] = Field(default_factory=dict, description="Accident count by time of day")
    disclaimer: str = Field("HISTORICAL ROAD RISK — NOT LIVE ACCIDENT DATA", description="Mandatory historical disclaimer")

class RoadAccidentTrendPoint(BaseModel):
    year: int = Field(..., description="Year")
    accident_count: int = Field(..., description="Accident count across North East India")

class RoadRiskIndex(BaseModel):
    state: str = Field(..., description="State name")
    risk_score: float = Field(..., description="Historical road risk score")
    risk_level: str = Field(..., description="Risk level: LOW | MODERATE | HIGH | CRITICAL")
    route_multiplier: float = Field(..., description="Route multiplier factor")
    disclaimer: str = Field("HISTORICAL ROAD RISK — NOT LIVE ACCIDENT DATA", description="Mandatory disclaimer")

class RoadAccidentAnalyticsResponse(BaseModel):
    metadata: Optional[Dict[str, Any]] = Field(None, description="Dataset metadata")
    state_baselines: Dict[str, StateRoadRiskStats] = Field(..., description="State-level baselines")
    risk_indices: List[RoadRiskIndex] = Field(default_factory=list, description="State risk index list")
    risk_factor_breakdown: Dict[str, float] = Field(default_factory=dict, description="Risk factor breakdown")
    annual_trend_series: List[RoadAccidentTrendPoint] = Field(default_factory=list, description="Multi-year trend series")
    severity_distribution: Dict[str, int] = Field(default_factory=dict, description="Severity counts")
    weather_distribution: Dict[str, int] = Field(default_factory=dict, description="Weather counts")
    road_type_distribution: Dict[str, int] = Field(default_factory=dict, description="Road type counts")
    time_of_day_distribution: Dict[str, int] = Field(default_factory=dict, description="Time of day counts")
    processed_records_count: int = Field(..., description="Processed record count")
    unmapped_records_count: int = Field(..., description="Unmapped national record count")
    disclaimer: str = Field("HISTORICAL ACCIDENT RISK — NOT LIVE INCIDENTS", description="Mandatory disclaimer")
