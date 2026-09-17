from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class RainfallMetadataResponse(BaseModel):
    dataset_name: str = Field(..., description="Dataset name")
    source_organization: str = Field(..., description="Source organization")
    original_upstream_url: str = Field(..., description="Original official catalog URL")
    kaggle_source_url: str = Field(..., description="Kaggle dataset URL")
    license: str = Field(..., description="Open data license")
    retrieval_date: str = Field(..., description="Retrieval date")
    coverage_period: str = Field(..., description="Coverage period (1901-2017)")
    neris_operational_scope: List[str] = Field(default_factory=list, description="North East India subdivisions")
    mapped_hubs_count: int = Field(15, description="Number of mapped logistics hubs")
    preprocessing_steps: List[str] = Field(default_factory=list, description="List of processing steps")
    disclaimer: str = Field("HISTORICAL RAINFALL — NOT LIVE WEATHER", description="Mandatory historical data disclaimer")
    status: str = Field("VALIDATED_AND_DERIVED", description="Ingestion validation status")

class SubdivisionRainfallStats(BaseModel):
    subdivision: str = Field(..., description="Subdivision name")
    region_code: str = Field(..., description="Region code e.g. NER_AM")
    states: List[str] = Field(default_factory=list, description="Associated North East states")
    primary_hubs: List[str] = Field(default_factory=list, description="Primary mapped hubs")
    coverage_years: str = Field("1901-2017", description="Coverage years")
    average_annual_mm: float = Field(..., description="117-year average annual rainfall in mm")
    average_monsoon_mm: float = Field(..., description="117-year average monsoon rainfall in mm (Jun-Sep)")
    monthly_means_mm: Dict[str, float] = Field(..., description="Monthly mean rainfall in mm")
    monthly_risk_indices: Dict[str, float] = Field(..., description="Normalized monthly risk indices (0.0 to 1.0)")

class RainfallTrendPoint(BaseModel):
    year: int = Field(..., description="Year")
    avg_annual_mm: float = Field(..., description="Average annual rainfall across North East India in mm")

class ExtremeRainfallRecord(BaseModel):
    rank: int = Field(..., description="Rank")
    subdivision: str = Field(..., description="Subdivision")
    year: int = Field(..., description="Year")
    annual_rainfall_mm: float = Field(..., description="Annual rainfall in mm")
    monsoon_rainfall_mm: float = Field(..., description="Monsoon rainfall in mm")
    disclaimer: str = Field("Historical High-Rainfall Record (1901-2017 IMD Baseline)", description="Record disclaimer")

class RainfallAnalyticsResponse(BaseModel):
    metadata: Optional[Dict[str, Any]] = Field(None, description="Dataset metadata")
    baselines: Dict[str, SubdivisionRainfallStats] = Field(..., description="Sub-divisional baselines")
    annual_trend_series: List[RainfallTrendPoint] = Field(default_factory=list, description="117-year annual trend points")
    extreme_rainfall_records: List[ExtremeRainfallRecord] = Field(default_factory=list, description="Top historical extreme rainfall years")
    processed_records_count: int = Field(..., description="Number of processed records")
    disclaimer: str = Field("HISTORICAL RAINFALL — NOT LIVE WEATHER. Multi-decade statistical baseline (1901–2017).", description="Mandatory historical disclaimer")

class SubdivisionRiskIndex(BaseModel):
    subdivision: str = Field(..., description="Subdivision name")
    region_code: str = Field(..., description="Region code")
    month: str = Field(..., description="Target month e.g. SEP")
    mean_rainfall_mm: float = Field(..., description="117-year mean rainfall for month in mm")
    risk_score: float = Field(..., description="Normalized risk index score (0.0 to 1.0)")
    risk_level: str = Field(..., description="Risk category: LOW | MODERATE | HIGH | CRITICAL")
    disclaimer: str = Field("HISTORICAL RAINFALL — NOT LIVE WEATHER", description="Mandatory historical disclaimer")
