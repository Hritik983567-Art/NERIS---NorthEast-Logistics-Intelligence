from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class HistoricalLandslideFloodMetadata(BaseModel):
    dataset_name: str = Field(..., description="Dataset name")
    source_organization: str = Field(..., description="Source organization")
    kaggle_source_url: str = Field(..., description="Kaggle URL")
    license: str = Field(..., description="License notice")
    retrieval_date: str = Field(..., description="Retrieval date")
    coverage_period: str = Field(..., description="Coverage period (2000-2023)")
    source_type: str = Field("historical_dataset", description="Source type tag")
    neris_operational_scope: List[str] = Field(default_factory=list, description="Scope")
    preprocessing_steps: List[str] = Field(default_factory=list, description="Preprocessing steps")
    disclaimer: str = Field("HISTORICAL DATASET EVENT (source_type = 'historical_dataset') — NOT LIVE VERIFIED INCIDENT", description="Disclaimer")
    status: str = Field("VALIDATED_AND_DERIVED", description="Status")

class HistoricalEventRecord(BaseModel):
    id: str = Field(..., description="Unique event ID")
    event_id: str = Field(..., description="Alias for ID")
    title: str = Field(..., description="Event title")
    event_type: str = Field(..., description="Event type: LANDSLIDE | FLASH_FLOOD | RIVERINE_FLOOD | MUDSLIDE")
    state: str = Field(..., description="State name")
    district: str = Field(..., description="District name")
    latitude: float = Field(..., description="GPS latitude")
    longitude: float = Field(..., description="GPS longitude")
    event_date: str = Field(..., description="Event date YYYY-MM-DD")
    year: int = Field(..., description="Year")
    severity: str = Field(..., description="Severity: CRITICAL | HIGH | MODERATE")
    trigger: str = Field(..., description="Disaster trigger e.g. Heavy Rain")
    fatalities: int = Field(0, description="Casualties count")
    data_type: str = Field("historical", description="Mandatory data type tag")
    source_type: str = Field("historical_dataset", description="Mandatory source type tag")
    source: str = Field(..., description="Source catalog attribution")
    disclaimer: str = Field("HISTORICAL DATASET EVENT (source_type = 'historical_dataset') — NOT LIVE VERIFIED INCIDENT", description="Mandatory disclaimer")
    historical_status: str = Field("RESEARCH_BASELINE_DATA", description="Status tag")

class EnvironmentalRiskIndexResponse(BaseModel):
    state: str = Field(..., description="Northeast state name")
    environmental_risk_score: float = Field(..., description="Calculated 0-100 environmental risk index")
    risk_level: str = Field(..., description="Risk category: LOW | MODERATE | HIGH | VERY_HIGH | EXTREME")
    landslide_count: int = Field(..., description="Historical landslide events count")
    flood_count: int = Field(..., description="Historical flood events count")
    total_count: int = Field(..., description="Total historical events count")
    data_type: str = Field("historical", description="Mandatory data_type='historical' tag")
    source_type: str = Field("historical_dataset", description="Mandatory source_type='historical_dataset' tag")
    disclaimer: str = Field("HISTORICAL DATASET EVENT (source_type = 'historical_dataset') — NOT LIVE VERIFIED INCIDENT", description="Mandatory disclaimer")

class EnvironmentalRiskSummaryResponse(BaseModel):
    total_events_count: int = Field(..., description="Total historical events")
    state_distribution: Dict[str, int] = Field(..., description="State event breakdown")
    event_type_distribution: Dict[str, int] = Field(..., description="Event type breakdown")
    severity_distribution: Dict[str, int] = Field(..., description="Severity breakdown")
    state_risk_scores: Dict[str, float] = Field(..., description="State risk index scores")
    data_type: str = Field("historical", description="Mandatory data_type tag")
    source_type: str = Field("historical_dataset", description="Mandatory source_type tag")
    disclaimer: str = Field("HISTORICAL DATASET EVENT (source_type = 'historical_dataset') — NOT LIVE VERIFIED INCIDENT", description="Mandatory disclaimer")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Dataset metadata")

class EnvironmentalRiskRegionDetailResponse(BaseModel):
    state: str = Field(..., description="State name")
    environmental_risk_score: float = Field(..., description="Environmental risk index score")
    risk_level: str = Field(..., description="Risk level classification")
    total_events: int = Field(..., description="Total events for region")
    events: List[HistoricalEventRecord] = Field(default_factory=list, description="Historical event records")
    data_type: str = Field("historical", description="Mandatory data_type tag")
    source_type: str = Field("historical_dataset", description="Mandatory source_type tag")
    disclaimer: str = Field("HISTORICAL DATASET EVENT (source_type = 'historical_dataset') — NOT LIVE VERIFIED INCIDENT", description="Mandatory disclaimer")

class EnvironmentalRiskTrendsResponse(BaseModel):
    yearly_distribution: Dict[str, int] = Field(..., description="Events by year")
    monthly_distribution: Dict[str, int] = Field(..., description="Events by month")
    event_type_trends: Dict[str, Dict[str, int]] = Field(..., description="Event types over time")
    data_type: str = Field("historical", description="Mandatory data_type tag")
    source_type: str = Field("historical_dataset", description="Mandatory source_type tag")
    disclaimer: str = Field("HISTORICAL DATASET EVENT (source_type = 'historical_dataset') — NOT LIVE VERIFIED INCIDENT", description="Mandatory disclaimer")

# Alias for backward compatibility
LandslideFloodAnalyticsResponse = EnvironmentalRiskSummaryResponse

