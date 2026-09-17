from enum import Enum
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, root_validator

class AlertSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"

class AlertStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    EXPIRED = "EXPIRED"

class NERISAlert(BaseModel):
    alertId: str = Field(..., description="Unique alert identifier e.g. ALT-8041")
    id: str = Field(..., description="Alias for alertId")
    type: str = Field("HAZARD_WARNING", description="Alert category type: HAZARD_WARNING | PROXIMITY_ALERT | OPERATIONAL_ALERT | DISASTER_EVACUATION")
    severity: str = Field("CRITICAL", description="Severity level: CRITICAL | HIGH | MODERATE | LOW")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message or operational description")
    description: Optional[str] = Field(None, description="Alias for message")
    incidentId: Optional[str] = Field(None, description="Originating incident ID")
    incident_id: Optional[str] = Field(None, description="Alias for incidentId")
    vehicleId: Optional[str] = Field(None, description="Associated vehicle ID")
    vehicle_id: Optional[str] = Field(None, description="Alias for vehicleId")
    recipientScope: str = Field("ALL_COMMANDERS", description="Target recipient scope: ALL_COMMANDERS | FIELD_OFFICERS | DISPATCHERS | PUBLIC_ADVISORY")
    createdAt: str = Field(..., description="ISO 8601 creation timestamp")
    created_at: str = Field(..., description="Alias for createdAt")
    status: str = Field("ACTIVE", description="Alert status: ACTIVE | ACKNOWLEDGED | RESOLVED | EXPIRED")
    
    acknowledged_by: Optional[str] = Field(None, description="Commander ID who acknowledged the alert")
    acknowledged_at: Optional[str] = Field(None, description="ISO 8601 timestamp of acknowledgment")
    resolved_by: Optional[str] = Field(None, description="Commander ID who resolved the alert")
    resolved_at: Optional[str] = Field(None, description="ISO 8601 timestamp of resolution")
    
    delivery_mode: str = Field("In-App Operational Alert (AWS DynamoDB)", description="Notification channel label")
    district: Optional[str] = Field("ASSAM", description="Affected district or state corridor")
    source: str = Field("NERIS Risk Evaluation Engine", description="Alert source department")

    @root_validator(pre=True)
    def resolve_alert_aliases(cls, values: dict):
        if not values:
            return values
        
        aid = str(values.get("alertId") or values.get("id") or f"ALT-{int(datetime.now().timestamp())}")
        atype = str(values.get("type") or "HAZARD_WARNING")
        sev = str(values.get("severity") or "CRITICAL").upper()
        title = str(values.get("title") or "Operational Alert")
        msg = str(values.get("message") or values.get("description") or "Active operational hazard detected.")
        inc_id = values.get("incidentId") or values.get("incident_id")
        veh_id = values.get("vehicleId") or values.get("vehicle_id")
        scope = str(values.get("recipientScope") or values.get("recipient_scope") or "ALL_COMMANDERS")
        
        ts = str(values.get("createdAt") or values.get("created_at") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        stat = str(values.get("status") or "ACTIVE").upper()

        values["alertId"] = aid
        values["id"] = aid
        values["type"] = atype
        values["severity"] = sev
        values["title"] = title
        values["message"] = msg
        values["description"] = msg
        values["incidentId"] = inc_id
        values["incident_id"] = inc_id
        values["vehicleId"] = veh_id
        values["vehicle_id"] = veh_id
        values["recipientScope"] = scope
        values["createdAt"] = ts
        values["created_at"] = ts
        values["status"] = stat
        return values

class CreateAlertRequest(BaseModel):
    type: Optional[str] = Field("HAZARD_WARNING", description="Alert type")
    severity: Optional[str] = Field("CRITICAL", description="Severity level")
    title: str = Field(..., description="Headline title")
    message: Optional[str] = Field(None, description="Detailed message")
    description: Optional[str] = Field(None, description="Alias for message")
    incidentId: Optional[str] = Field(None, description="Incident ID")
    incident_id: Optional[str] = Field(None, description="Alias for incidentId")
    vehicleId: Optional[str] = Field(None, description="Vehicle ID")
    vehicle_id: Optional[str] = Field(None, description="Alias for vehicleId")
    recipientScope: Optional[str] = Field("ALL_COMMANDERS", description="Recipient scope")
    district: Optional[str] = Field("ASSAM", description="District or location")

class UpdateAlertStatusRequest(BaseModel):
    status: str = Field(..., description="New alert status: ACTIVE | ACKNOWLEDGED | RESOLVED | EXPIRED")
    commander_id: Optional[str] = Field(None, description="Officer ID making change")
    notes: Optional[str] = Field(None, description="Operational notes")

class IncidentEvaluationRequest(BaseModel):
    incident_id: Optional[str] = Field(None, description="Incident ID")
    id: Optional[str] = Field(None, description="Alias for Incident ID")
    title: str = Field(..., description="Incident title or hazard type")
    severity: str = Field("CRITICAL", description="Incident severity level")
    district: str = Field("ASSAM", description="State or district location")
    description: Optional[str] = Field("", description="Detailed incident description")
    estimated_blockage_pct: Optional[float] = Field(80.0, description="Estimated highway blockage percentage")
    reporter: Optional[str] = Field("Field Inspector", description="Reporting officer name")

    def get_incident_id(self) -> str:
        return self.incident_id or self.id or f"INC-{int(datetime.now().timestamp())}"

class AlertActionRequest(BaseModel):
    commander_id: Optional[str] = Field(None, description="Authorized Commander officer ID or badge ID")
    action_by: Optional[str] = Field(None, description="Alias for Commander ID")
    commander_name: Optional[str] = Field(None, description="Authorized Commander name")
    notes: Optional[str] = Field(None, description="Optional resolution or operational notes")

    def get_commander_id(self) -> str:
        return self.commander_id or self.action_by or self.commander_name or "Cmdr. R. Gogoi"

class SOSDispatchPayload(BaseModel):
    vehicle_id: str = Field(..., description="Target supply convoy or vehicle identifier e.g. NER-MED-8041")
    reason: str = Field(..., description="Operational emergency dispatch reason e.g. Urgent medical escort required through landslide zone")
    location: Optional[str] = Field("NER Emergency Transit Corridor", description="Current location or route segment")
    severity: Optional[str] = Field("CRITICAL", description="Emergency severity level: CRITICAL | HIGH")

class SOSDispatchResponse(BaseModel):
    alert_id: str = Field(..., description="Generated persistent alert ID e.g. ALT-SOS-1789283863")
    vehicle_id: str = Field(..., description="Associated convoy vehicle ID")
    status: str = Field("EMERGENCY_DISPATCH", description="Updated fleet vehicle status")
    dispatched_at: str = Field(..., description="ISO 8601 UTC dispatch timestamp")
    dispatched_by: str = Field(..., description="Authenticated officer ID or username who dispatched SOS")
    dynamodb_confirmed: bool = Field(True, description="True if alert persisted to Amazon DynamoDB table 'ner_alerts'")
    alert: NERISAlert = Field(..., description="Full persisted NERIS alert object")

