from enum import Enum
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    INFO = "INFO"
    UNKNOWN = "UNKNOWN"

class RecordCategory(str, Enum):
    NEWS = "NEWS"
    WEATHER = "WEATHER"
    DISASTER = "DISASTER"
    GOVT_NOTICE = "GOVT_NOTICE"
    ROAD_CONDITION = "ROAD_CONDITION"

class LocationMetadata(BaseModel):
    state: Optional[str] = Field(None, description="State name, e.g., Meghalaya")
    district: Optional[str] = Field(None, description="District name, e.g., East Khasi Hills")
    highway_id: Optional[str] = Field(None, description="Highway corridor ID, e.g., NH-06")
    hub_name: Optional[str] = Field(None, description="Transportation hub name, e.g., Shillong")
    lat: Optional[float] = Field(None, ge=-90.0, le=90.0, description="GPS Latitude")
    lng: Optional[float] = Field(None, ge=-180.0, le=180.0, description="GPS Longitude")

class ExternalRecord(BaseModel):
    id: str = Field(..., description="Unique record identifier")
    category: RecordCategory = Field(..., description="Domain category")
    source: str = Field(..., description="External publisher / provider name")
    source_url: str = Field(..., description="Direct origin URL or API endpoint")
    retrieved_at: str = Field(..., description="ISO 8601 timestamp of backend retrieval")
    published_at: Optional[str] = Field(None, description="ISO 8601 timestamp of original publication")
    title: str = Field(..., description="Title or headline")
    content_summary: str = Field(..., description="Detailed content or advisory text")
    location: LocationMetadata = Field(default_factory=LocationMetadata, description="Location metadata")
    severity: SeverityLevel = Field(SeverityLevel.INFO, description="Severity rating")
    is_live: bool = Field(False, description="True only if live fetched from external provider. False if static/historical.")
    extra_metadata: Dict[str, Any] = Field(default_factory=dict, description="Domain-specific metrics (e.g. temp_c, wind_speed, blockage_pct)")

class AdapterFetchResult(BaseModel):
    provider_name: str = Field(..., description="Adapter provider name")
    category: RecordCategory = Field(..., description="Record category")
    is_available: bool = Field(True, description="True if provider API responded successfully")
    total_records: int = Field(0, description="Count of retrieved records")
    records: List[ExternalRecord] = Field(default_factory=list, description="List of standardized records")
    error_message: Optional[str] = Field(None, description="Error message if provider unavailable")
    retrieved_at: str = Field(..., description="ISO 8601 retrieval timestamp")

class ExternalDataResponse(BaseModel):
    status: str = Field("SUCCESS", description="Response status")
    is_available: bool = Field(True, description="True if at least one live provider responded")
    total_results: int = Field(0, description="Total record count")
    records: List[ExternalRecord] = Field(default_factory=list, description="Combined standardized records")
    crawled_at: str = Field(..., description="Backend execution timestamp")
    provider_summary: Dict[str, Any] = Field(default_factory=dict, description="Summary of provider statuses")
