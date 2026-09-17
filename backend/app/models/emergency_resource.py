from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator

class EmergencyResourceMetadata(BaseModel):
    dataset_name: str = Field(..., description="Dataset name")
    source_organization: str = Field(..., description="Source organization")
    kaggle_source_url: str = Field(..., description="Kaggle URL")
    license: str = Field(..., description="License notice")
    license_verified: bool = Field(True, description="License verification flag")
    retrieval_date: str = Field(..., description="Retrieval date")
    coverage_period: str = Field(..., description="Coverage period (2022-2026)")
    source_type: str = Field("historical_dataset", description="Source type tag")
    data_type: str = Field("historical", description="Data type tag")
    neris_operational_scope: List[str] = Field(default_factory=list, description="Scope")
    resource_categories: List[str] = Field(default_factory=list, description="Resource categories")
    preprocessing_steps: List[str] = Field(default_factory=list, description="Preprocessing steps")
    disclaimer: str = Field("HISTORICAL RESOURCE DATA (source_type = 'historical_dataset', data_type = 'historical') — NOT LIVE AVAILABILITY", description="Disclaimer")
    status: str = Field("VALIDATED_AND_DERIVED", description="Status")

class EmergencyResourceRecord(BaseModel):
    id: str = Field(..., description="Unique resource ID")
    resource_id: str = Field(..., description="Alias for resource ID")
    name: str = Field(..., description="Facility or resource name")
    type: str = Field(..., description="Normalized resource category: HOSPITAL | WAREHOUSE | SHELTER | TRANSPORT")
    source_resource_type: str = Field(..., description="Original raw category from dataset")
    resource_type: str = Field(..., description="Alias for type")
    state: str = Field(..., description="State name")
    district: str = Field(..., description="District name")
    latitude: float = Field(..., description="GPS latitude")
    longitude: float = Field(..., description="GPS longitude")
    capacity_bed_or_sqm: int = Field(0, description="Total recorded capacity")
    capacity: int = Field(0, description="Alias for capacity_bed_or_sqm")
    historical_available_capacity: int = Field(0, description="Historical recorded available capacity snapshot")
    available_capacity: int = Field(0, description="Alias for historical_available_capacity")
    operational_status: str = Field("OPERATIONAL", description="Recorded operational status")
    source_organization: str = Field(..., description="Source organization attribution")
    contact_phone: Optional[str] = Field(None, description="Contact phone or None")
    last_updated: str = Field(..., description="Record update date")
    source_type: str = Field("historical_dataset", description="Mandatory source_type tag")
    data_type: str = Field("historical", description="Mandatory data_type tag")
    disclaimer: str = Field("HISTORICAL RESOURCE DATA (source_type = 'historical_dataset', data_type = 'historical') — NOT LIVE AVAILABILITY", description="Mandatory disclaimer")

    @validator('latitude')
    def validate_latitude(cls, v):
        if not (-90.0 <= v <= 90.0):
            raise ValueError(f"Latitude out of bounds: {v}")
        return v

    @validator('longitude')
    def validate_longitude(cls, v):
        if not (-180.0 <= v <= 180.0):
            raise ValueError(f"Longitude out of bounds: {v}")
        return v

class EmergencyResourceCoverageResponse(BaseModel):
    state: str = Field(..., description="State name")
    resource_coverage_score: float = Field(..., description="Calculated 0-100 historical resource coverage score")
    coverage_level: str = Field(..., description="Classification: CRITICAL_DEFICIT | LOW | MODERATE | GOOD | EXCELLENT")
    total_resources: int = Field(..., description="Total historical resources in state")
    total_capacity: int = Field(..., description="Total recorded capacity in state")
    data_type: str = Field("historical", description="Mandatory data_type tag")
    source_type: str = Field("historical_dataset", description="Mandatory source_type tag")
    disclaimer: str = Field("HISTORICAL RESOURCE DATA — NOT LIVE AVAILABILITY", description="Mandatory disclaimer")

class EmergencyResourceSummaryResponse(BaseModel):
    total_resources: int = Field(..., description="Total historical resources count")
    total_resources_count: int = Field(..., description="Total historical resources count alias")
    total_capacity: int = Field(..., description="Total recorded capacity across all resources")
    average_coverage_score: float = Field(..., description="Average historical resource coverage score across NE")
    state_distribution: Dict[str, int] = Field(..., description="Resource count by state")
    type_distribution: Dict[str, int] = Field(..., description="Resource count by type")
    state_capacity: Dict[str, int] = Field(..., description="Total capacity by state")
    state_coverage_scores: Dict[str, float] = Field(..., description="State historical resource coverage scores (0-100)")
    data_type: str = Field("historical", description="Mandatory data_type tag")
    source_type: str = Field("historical_dataset", description="Mandatory source_type tag")
    disclaimer: str = Field("HISTORICAL RESOURCE DATA — NOT LIVE AVAILABILITY", description="Mandatory disclaimer")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Dataset metadata")

class EmergencyResourceRegionDetailResponse(BaseModel):
    state: str = Field(..., description="State name")
    resource_coverage_score: float = Field(..., description="Resource coverage index score")
    coverage_level: str = Field(..., description="Coverage level classification")
    total_resources: int = Field(..., description="Total historical resources for state")
    total_capacity: int = Field(..., description="Total capacity for state")
    resources: List[EmergencyResourceRecord] = Field(default_factory=list, description="List of historical resource records")
    data_type: str = Field("historical", description="Mandatory data_type tag")
    source_type: str = Field("historical_dataset", description="Mandatory source_type tag")
    disclaimer: str = Field("HISTORICAL RESOURCE DATA — NOT LIVE AVAILABILITY", description="Mandatory disclaimer")

class EmergencyResourceTrendsResponse(BaseModel):
    yearly_distribution: Dict[str, int] = Field(..., description="Resources recorded by baseline year")
    type_trends: Dict[str, Dict[str, int]] = Field(..., description="Resource categories over time")
    data_type: str = Field("historical", description="Mandatory data_type tag")
    source_type: str = Field("historical_dataset", description="Mandatory source_type tag")
    disclaimer: str = Field("HISTORICAL RESOURCE DATA — NOT LIVE AVAILABILITY", description="Mandatory disclaimer")
