from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class IncidentType(str, Enum):
    LANDSLIDE = "LANDSLIDE"
    FLOOD = "FLOOD"
    ROAD_BLOCKAGE = "ROAD_BLOCKAGE"
    BRIDGE_DAMAGE = "BRIDGE_DAMAGE"
    ACCIDENT = "ACCIDENT"
    WEATHER = "WEATHER"
    OTHER = "OTHER"

class IncidentSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"

class EvidenceStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PENDING = "PENDING"
    FAILED = "FAILED"
    NONE = "NONE"

class NERISIncident(BaseModel):
    id: str = Field(..., description="Unique incident ID e.g. INC-2026-8041")
    title: str = Field(..., description="Incident title or headline")
    type: IncidentType = Field(IncidentType.LANDSLIDE, description="Incident classification type")
    severity: IncidentSeverity = Field(IncidentSeverity.CRITICAL, description="Severity rating")
    description: str = Field("", description="Detailed incident description and clearance notes")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Geo-Latitude coordinate")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Geo-Longitude coordinate")
    reporter: str = Field("Field Inspector", description="Reporting officer ID or name")
    timestamp: str = Field(..., description="ISO 8601 creation timestamp")
    status: str = Field("SUBMITTED", description="Incident status: SUBMITTED | SYNCED | PENDING | FAILED")
    
    # Evidence Media Fields
    evidence_status: EvidenceStatus = Field(EvidenceStatus.NONE, description="Amazon S3 upload status: UPLOADED | PENDING | FAILED | NONE")
    evidence_url: str = Field("", description="Amazon S3 object URL or fallback reference")
    uploaded_at: Optional[str] = Field(None, description="ISO 8601 evidence upload timestamp")
    district: Optional[str] = Field("ASSAM", description="Affected state or district corridor")
    location_name: Optional[str] = Field("NER Corridor", description="Landmark location name")

class IncidentCreateRequest(BaseModel):
    id: Optional[str] = Field(None, description="Optional incident ID alias")
    title: str = Field(..., description="Incident title or headline")
    type: Optional[str] = Field("LANDSLIDE", description="Incident classification type")
    severity: Optional[str] = Field("CRITICAL", description="Severity rating")
    description: Optional[str] = Field("", description="Detailed description")
    state: Optional[str] = Field("ASSAM", description="State or district")
    district: Optional[str] = Field("ASSAM", description="District")
    locationName: Optional[str] = Field(None, description="Location landmark")
    location_name: Optional[str] = Field(None, description="Location landmark alias")
    lat: float = Field(..., ge=-90.0, le=90.0, description="Geo-Latitude coordinate")
    lng: float = Field(..., ge=-180.0, le=180.0, description="Geo-Longitude coordinate")
    reporter: Optional[str] = Field("Field Officer", description="Reporting officer name")
    photoUrl: Optional[str] = Field(None, description="Evidence photo URL")
    evidence_url: Optional[str] = Field(None, description="Evidence photo URL alias")
    evidence_status: Optional[str] = Field("NONE", description="S3 evidence upload status")
    uploaded_at: Optional[str] = Field(None, description="ISO timestamp of photo upload")
