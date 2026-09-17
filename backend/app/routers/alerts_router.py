from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException, status, Depends, Request
from app.models.alert import (
    NERISAlert, IncidentEvaluationRequest, AlertActionRequest, CreateAlertRequest, UpdateAlertStatusRequest, SOSDispatchPayload, SOSDispatchResponse
)
from app.services.alert_service import get_alert_service
from app.core.dependencies import require_roles

router = APIRouter(tags=["Command Center Alert Hub API"])

@router.get("/alerts", response_model=List[NERISAlert], status_code=status.HTTP_200_OK)
@router.get("/api/alerts", response_model=List[NERISAlert], status_code=status.HTTP_200_OK)
@router.get("/api/v1/alerts", response_model=List[NERISAlert], status_code=status.HTTP_200_OK)
async def get_command_center_alerts(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter alerts by status: ACTIVE, ACKNOWLEDGED, RESOLVED"),
    severity: Optional[str] = Query(None, description="Filter alerts by severity: CRITICAL, HIGH, MODERATE, LOW")
):
    """
    Retrieves all persistent Command Center alerts from AWS DynamoDB ('ner_alerts').
    """
    service = get_alert_service()
    return service.get_all_alerts(status_filter=status_filter, severity_filter=severity)

@router.post("/alerts", response_model=NERISAlert, status_code=status.HTTP_201_CREATED)
@router.post("/api/alerts", response_model=NERISAlert, status_code=status.HTTP_201_CREATED)
@router.post("/api/v1/alerts", response_model=NERISAlert, status_code=status.HTTP_201_CREATED)
async def create_command_center_alert(
    payload: Dict[str, Any],
    user: Dict[str, Any] = Depends(require_roles(["FIELD_OFFICER", "COMMANDER", "ADMIN"]))
):
    """
    Creates and persists a new Command Center operational alert into AWS DynamoDB.
    """
    if not payload.get("title"):
        raise HTTPException(status_code=400, detail="Validation Error: Alert 'title' is required.")

    req = CreateAlertRequest(
        type=payload.get("type", "HAZARD_WARNING"),
        severity=payload.get("severity", "CRITICAL"),
        title=payload.get("title"),
        message=payload.get("message") or payload.get("description"),
        description=payload.get("description") or payload.get("message"),
        incidentId=payload.get("incidentId") or payload.get("incident_id"),
        incident_id=payload.get("incident_id") or payload.get("incidentId"),
        vehicleId=payload.get("vehicleId") or payload.get("vehicle_id"),
        vehicle_id=payload.get("vehicle_id") or payload.get("vehicleId"),
        recipientScope=payload.get("recipientScope") or payload.get("recipient_scope") or "ALL_COMMANDERS",
        district=payload.get("district", "ASSAM")
    )
    service = get_alert_service()
    alert = service.create_alert(req)
    return alert

@router.patch("/alerts/{alert_id}", response_model=NERISAlert, status_code=status.HTTP_200_OK)
@router.patch("/api/alerts/{alert_id}", response_model=NERISAlert, status_code=status.HTTP_200_OK)
@router.patch("/api/v1/alerts/{alert_id}", response_model=NERISAlert, status_code=status.HTTP_200_OK)
@router.patch("/alerts/{alert_id}/status", response_model=NERISAlert, status_code=status.HTTP_200_OK)
@router.patch("/api/alerts/{alert_id}/status", response_model=NERISAlert, status_code=status.HTTP_200_OK)
@router.patch("/api/v1/alerts/{alert_id}/status", response_model=NERISAlert, status_code=status.HTTP_200_OK)
async def update_alert_status(
    alert_id: str,
    payload: Dict[str, Any],
    user: Dict[str, Any] = Depends(require_roles(["COMMANDER", "ADMIN"]))
):
    """
    Updates the status of an operational alert (ACTIVE -> ACKNOWLEDGED / RESOLVED / EXPIRED) and persists to DynamoDB.
    """
    new_status = payload.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="Validation Error: 'status' is required for alert status update.")

    commander_id = payload.get("commander_id") or payload.get("action_by") or payload.get("commander_name") or user.get("sub", "Commander")
    notes = payload.get("notes")

    service = get_alert_service()
    updated_alert = service.update_alert_status(alert_id, new_status, commander_id=commander_id, notes=notes)
    if not updated_alert:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found.")
    return updated_alert

@router.post("/alerts/evaluate-incident", status_code=status.HTTP_200_OK)
@router.post("/api/alerts/evaluate-incident", status_code=status.HTTP_200_OK)
@router.post("/api/v1/alerts/evaluate-incident", status_code=status.HTTP_200_OK)
async def evaluate_incident_risk(req: IncidentEvaluationRequest):
    """
    Incident Workflow Step 2 & 3:
    Evaluates incident risk parameters and generates a Command Center alert if critical/high risk.
    """
    service = get_alert_service()
    alert = service.evaluate_incident_and_create_alert(req)
    if not alert:
        return {
            "status": "EVALUATED_NO_ALERT",
            "message": f"Incident '{req.incident_id}' risk evaluated below alert threshold.",
            "alert": None
        }
    return {
        "status": "ALERT_GENERATED",
        "message": f"Command Center alert '{alert.id}' generated for incident '{req.incident_id}'.",
        "alert": alert
    }

@router.patch("/alerts/{alert_id}/acknowledge", response_model=NERISAlert, status_code=status.HTTP_200_OK)
@router.patch("/api/alerts/{alert_id}/acknowledge", response_model=NERISAlert, status_code=status.HTTP_200_OK)
@router.patch("/api/v1/alerts/{alert_id}/acknowledge", response_model=NERISAlert, status_code=status.HTTP_200_OK)
async def acknowledge_alert(
    alert_id: str,
    req: AlertActionRequest,
    user: Dict[str, Any] = Depends(require_roles(["COMMANDER", "ADMIN"]))
):
    """
    Updates alert status from ACTIVE -> ACKNOWLEDGED by an authorized Commander.
    """
    commander_id = req.get_commander_id()
    service = get_alert_service()
    alert = service.acknowledge_alert(alert_id, commander_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found.")
    return alert

@router.patch("/alerts/{alert_id}/resolve", response_model=NERISAlert, status_code=status.HTTP_200_OK)
@router.patch("/api/alerts/{alert_id}/resolve", response_model=NERISAlert, status_code=status.HTTP_200_OK)
@router.patch("/api/v1/alerts/{alert_id}/resolve", response_model=NERISAlert, status_code=status.HTTP_200_OK)
async def resolve_alert(
    alert_id: str,
    req: AlertActionRequest,
    user: Dict[str, Any] = Depends(require_roles(["COMMANDER", "ADMIN"]))
):
    """
    Updates alert status to RESOLVED by an authorized Commander.
    """
    commander_id = req.get_commander_id()
    service = get_alert_service()
    alert = service.resolve_alert(alert_id, commander_id, notes=req.notes)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found.")
    return alert

@router.post("/alerts/sos-dispatch", response_model=SOSDispatchResponse, status_code=status.HTTP_201_CREATED)
@router.post("/api/alerts/sos-dispatch", response_model=SOSDispatchResponse, status_code=status.HTTP_201_CREATED)
@router.post("/api/v1/alerts/sos-dispatch", response_model=SOSDispatchResponse, status_code=status.HTTP_201_CREATED)
async def dispatch_emergency_sos(
    payload: SOSDispatchPayload,
    user: Dict[str, Any] = Depends(require_roles(["FIELD_OFFICER", "COMMANDER", "DISPATCHER", "ADMIN"]))
):
    """
    Dispatches a real-time emergency SOS vector alert for a convoy vehicle.
    Persists alert into AWS DynamoDB ('ner_alerts'), updates fleet status, and returns dispatch response.
    """
    if not payload.vehicle_id:
        raise HTTPException(status_code=400, detail="Validation Error: 'vehicle_id' is required for emergency SOS dispatch.")
    if not payload.reason:
        raise HTTPException(status_code=400, detail="Validation Error: 'reason' is required for emergency SOS dispatch.")

    service = get_alert_service()
    response = service.dispatch_sos_alert(payload, user)
    return response


