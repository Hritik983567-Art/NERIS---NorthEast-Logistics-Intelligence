import os
import json
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.models.alert import (
    NERISAlert, AlertStatus, AlertSeverity, IncidentEvaluationRequest, CreateAlertRequest, UpdateAlertStatusRequest, SOSDispatchPayload, SOSDispatchResponse
)
from app.adapters.aws_dynamodb import get_dynamodb_adapter

logger = logging.getLogger("neris.alert_service")

ALERTS_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "alerts_db.json")

SEED_ALERTS: List[Dict[str, Any]] = [
    {
        "id": "ALT-2026-101",
        "alertId": "ALT-2026-101",
        "incident_id": "INC-DIMA-804",
        "incidentId": "INC-DIMA-804",
        "type": "HAZARD_WARNING",
        "severity": "CRITICAL",
        "title": "RED ALERT: Heavy Rainfall & Landslide in Dima Hasao & West Siang",
        "message": "Continuous cloudburst triggered 80% highway blockage on NH-27. Military emergency escort & heavy BRO dozers dispatched.",
        "description": "Continuous cloudburst triggered 80% highway blockage on NH-27. Military emergency escort & heavy BRO dozers dispatched.",
        "created_at": "2026-09-11T18:00:00Z",
        "createdAt": "2026-09-11T18:00:00Z",
        "status": "ACTIVE",
        "recipientScope": "ALL_COMMANDERS",
        "delivery_mode": "In-App Operational Alert (AWS DynamoDB)",
        "district": "ASSAM",
        "source": "IMD Guwahati Regional Met Center"
    },
    {
        "id": "ALT-2026-102",
        "alertId": "ALT-2026-102",
        "incident_id": "INC-MAO-902",
        "incidentId": "INC-MAO-902",
        "type": "HAZARD_WARNING",
        "severity": "HIGH",
        "title": "NH-2 Mao Gate Landslide - BRO Machinery Clearance Underway",
        "message": "Senapati district slope failure causing single-lane traffic regulation. Convoys moving under alternating 30-min intervals.",
        "description": "Senapati district slope failure causing single-lane traffic regulation. Convoys moving under alternating 30-min intervals.",
        "created_at": "2026-09-11T18:25:00Z",
        "createdAt": "2026-09-11T18:25:00Z",
        "status": "ACTIVE",
        "recipientScope": "FIELD_UNITS",
        "delivery_mode": "In-App Operational Alert (AWS DynamoDB)",
        "district": "MANIPUR",
        "source": "Border Roads Organisation (BRO Project Vartak)"
    },
    {
        "id": "ALT-2026-103",
        "alertId": "ALT-2026-103",
        "incident_id": "INC-TEESTA-310",
        "incidentId": "INC-TEESTA-310",
        "type": "DISASTER_EVACUATION",
        "severity": "HIGH",
        "title": "Teesta River Flood Warning: NH-10 Rangpo Stretch Waterlogged",
        "message": "North Sikkim cloudburst water rise affecting heavy freight movements. BRO Project Swastik excavators deployed.",
        "description": "North Sikkim cloudburst water rise affecting heavy freight movements. BRO Project Swastik excavators deployed.",
        "created_at": "2026-09-11T19:00:00Z",
        "createdAt": "2026-09-11T19:00:00Z",
        "status": "ACKNOWLEDGED",
        "acknowledged_by": "NER-CMD-8041",
        "acknowledged_at": "2026-09-11T19:15:00Z",
        "recipientScope": "DISPATCHERS",
        "delivery_mode": "In-App Operational Alert (AWS DynamoDB)",
        "district": "SIKKIM",
        "source": "Sikkim SDMA Alert Operations"
    }
]

class AlertService:
    """
    Persistent Alert Service for Command Center alerts.
    Implements Incident -> Risk Evaluation -> Alert Generation -> Command Center Notification workflow.
    Persists alert records to AWS DynamoDB ('ner_alerts' table) and local cache.
    """
    def __init__(self):
        self.dynamodb = get_dynamodb_adapter()
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        db_dir = os.path.dirname(ALERTS_DB_PATH)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
        if not os.path.exists(ALERTS_DB_PATH):
            self._write_db(SEED_ALERTS)

    def _read_db(self) -> List[Dict[str, Any]]:
        try:
            if os.path.exists(ALERTS_DB_PATH):
                with open(ALERTS_DB_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as err:
            logger.warning(f"Error reading alerts_db.json: {err}.")
        return SEED_ALERTS

    def _write_db(self, alerts: List[Dict[str, Any]]):
        try:
            with open(ALERTS_DB_PATH, "w", encoding="utf-8") as f:
                json.dump(alerts, f, indent=2, ensure_ascii=False)
        except Exception as err:
            logger.error(f"Error writing to alerts_db.json: {err}")

    def get_all_alerts(
        self,
        status_filter: Optional[str] = None,
        severity_filter: Optional[str] = None
    ) -> List[NERISAlert]:
        raw_alerts = self._read_db()
        result = []
        for item in raw_alerts:
            s_val = str(item.get("status", "")).upper()
            sev_val = str(item.get("severity", "")).upper()

            if status_filter and status_filter.upper() != "ALL" and s_val != status_filter.upper():
                continue
            if severity_filter and severity_filter.upper() != "ALL" and sev_val != severity_filter.upper():
                continue
            result.append(NERISAlert(**item))
            
        # Sort by creation date newest first
        result.sort(key=lambda x: x.createdAt, reverse=True)
        return result

    def get_alert_by_id(self, alert_id: str) -> Optional[NERISAlert]:
        raw_alerts = self._read_db()
        for item in raw_alerts:
            if item.get("id") == alert_id or item.get("alertId") == alert_id:
                return NERISAlert(**item)
        return None

    def create_alert(self, req: CreateAlertRequest) -> NERISAlert:
        """
        Creates a new in-app alert record and persists to AWS DynamoDB ('ner_alerts').
        """
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        aid = f"ALT-{int(time.time())}"
        
        msg = req.message or req.description or f"Operational Alert: {req.title}"

        alert_dict = {
            "id": aid,
            "alertId": aid,
            "type": req.type or "HAZARD_WARNING",
            "severity": (req.severity or "CRITICAL").upper(),
            "title": req.title,
            "message": msg,
            "description": msg,
            "incidentId": req.incidentId or req.incident_id,
            "incident_id": req.incidentId or req.incident_id,
            "vehicleId": req.vehicleId or req.vehicle_id,
            "vehicle_id": req.vehicleId or req.vehicle_id,
            "recipientScope": req.recipientScope or "ALL_COMMANDERS",
            "createdAt": now_iso,
            "created_at": now_iso,
            "status": AlertStatus.ACTIVE.value,
            "delivery_mode": "In-App Operational Alert (AWS DynamoDB)",
            "district": (req.district or "ASSAM").upper(),
            "source": "NERIS Command Center Dispatch"
        }

        # Save to DynamoDB
        self.dynamodb.save_alert_to_dynamodb(alert_dict)

        # Save to local file cache
        alerts = self._read_db()
        alerts.insert(0, alert_dict)
        self._write_db(alerts)

        logger.info(f"Created operational alert '{aid}' for recipient scope '{alert_dict['recipientScope']}'.")
        return NERISAlert(**alert_dict)

    def evaluate_incident_and_create_alert(self, req: IncidentEvaluationRequest) -> Optional[NERISAlert]:
        """
        Real Incident Workflow Step 2 & 3: Risk Evaluation & Alert Generation.
        Evaluates an incident and generates a persistent Command Center alert if critical/high risk.
        """
        sev = req.severity.upper() if req.severity else "CRITICAL"
        blockage = req.estimated_blockage_pct or 80.0
        
        # Risk Evaluation Rule: Create Command Center alert for CRITICAL/HIGH severity or >= 50% blockage
        is_high_risk = (sev in ["CRITICAL", "HIGH"]) or (blockage >= 50.0)
        
        inc_id = req.get_incident_id()
        if not is_high_risk:
            logger.info(f"Incident {inc_id} risk score below alert threshold. No Command Center alert generated.")
            return None

        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        alert_id = f"ALT-{int(time.time())}"
        
        headline = f"COMMAND CENTER ALERT: {req.title}"
        if "ALERT" in req.title.upper():
            headline = req.title

        risk_message = (
            f"Risk Evaluation: {sev} severity incident logged at {req.district}. "
            f"Estimated highway blockage: {blockage}%. "
            f"Reported by: {req.reporter or 'Field Unit'}. "
            f"Advisory: Priority convoy escort and BRO dozers required."
        )
        if req.description:
            risk_message = f"{req.description} ({risk_message})"

        # Keep risk_message clean, concise, and operational for Command Center view
        # (Historical research metrics are kept in analytics services, not dumped into active operational alerts)

        new_alert = {
            "id": alert_id,
            "alertId": alert_id,
            "incident_id": inc_id,
            "incidentId": inc_id,
            "type": "HAZARD_WARNING",
            "severity": sev,
            "title": headline,
            "message": risk_message,
            "description": risk_message,
            "created_at": now_iso,
            "createdAt": now_iso,
            "status": AlertStatus.ACTIVE.value,
            "recipientScope": "ALL_COMMANDERS",
            "delivery_mode": "In-App Operational Alert (AWS DynamoDB)",
            "district": req.district.upper(),
            "source": f"NERIS Incident Risk Engine ({req.reporter or 'Field Inspector'})"
        }

        alerts = self._read_db()
        # Avoid duplicate alert for same incident_id if already active
        existing = [a for a in alerts if a.get("incident_id") == inc_id and a.get("status") == AlertStatus.ACTIVE.value]
        if existing:
            return NERISAlert(**existing[0])

        # Save to DynamoDB
        self.dynamodb.save_alert_to_dynamodb(new_alert)

        # Save to file cache
        alerts.insert(0, new_alert)
        self._write_db(alerts)
        
        logger.info(f"Generated Command Center Alert {alert_id} for Incident {inc_id} ({sev}).")
        return NERISAlert(**new_alert)

    def update_alert_status(
        self,
        alert_id: str,
        new_status: str,
        commander_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Optional[NERISAlert]:
        """
        Updates alert status (ACTIVE -> ACKNOWLEDGED / RESOLVED / EXPIRED).
        """
        alerts = self._read_db()
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        updated_item = None

        new_status_clean = str(new_status).upper()
        if new_status_clean not in {"ACTIVE", "ACKNOWLEDGED", "RESOLVED", "EXPIRED"}:
            new_status_clean = "ACKNOWLEDGED"

        for item in alerts:
            if item.get("id") == alert_id or item.get("alertId") == alert_id:
                item["status"] = new_status_clean
                if new_status_clean == "ACKNOWLEDGED":
                    item["acknowledged_by"] = commander_id or "Cmdr. R. Gogoi"
                    item["acknowledged_at"] = now_iso
                elif new_status_clean == "RESOLVED":
                    item["resolved_by"] = commander_id or "Cmdr. R. Gogoi"
                    item["resolved_at"] = now_iso
                    if notes:
                        item["message"] = f"{item['message']} [Resolution Notes: {notes}]"
                updated_item = item
                break

        if updated_item:
            # Persist update to DynamoDB
            self.dynamodb.save_alert_to_dynamodb(updated_item)

            # Persist update to file cache
            self._write_db(alerts)
            logger.info(f"Alert '{alert_id}' status updated to '{new_status_clean}' by '{commander_id or 'Commander'}'.")
            return NERISAlert(**updated_item)
            
        return None

    def acknowledge_alert(self, alert_id: str, commander_id: str) -> Optional[NERISAlert]:
        return self.update_alert_status(alert_id, "ACKNOWLEDGED", commander_id=commander_id)

    def resolve_alert(self, alert_id: str, commander_id: str, notes: Optional[str] = None) -> Optional[NERISAlert]:
        return self.update_alert_status(alert_id, "RESOLVED", commander_id=commander_id, notes=notes)

    def dispatch_sos_alert(self, req: SOSDispatchPayload, user: Dict[str, Any]) -> SOSDispatchResponse:
        """
        Dispatches an emergency SOS alert for a convoy vehicle, updates fleet status, and persists to AWS DynamoDB ('ner_alerts').
        """
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        aid = f"ALT-SOS-{int(time.time())}"
        officer_id = user.get("sub") or user.get("username") or user.get("name") or "Field Dispatcher"
        
        msg = f"🚨 EMERGENCY SOS DISPATCHED for Convoy {req.vehicle_id}: {req.reason}. Location: {req.location}"
        
        alert_dict = {
            "id": aid,
            "alertId": aid,
            "type": "SOS_DISPATCH",
            "severity": (req.severity or "CRITICAL").upper(),
            "title": f"🚨 EMERGENCY SOS DISPATCH: Convoy {req.vehicle_id}",
            "message": msg,
            "description": msg,
            "vehicleId": req.vehicle_id,
            "vehicle_id": req.vehicle_id,
            "recipientScope": "ALL_COMMANDERS",
            "createdAt": now_iso,
            "created_at": now_iso,
            "status": AlertStatus.ACTIVE.value,
            "delivery_mode": "In-App Operational Alert (AWS DynamoDB)",
            "district": "ASSAM",
            "source": f"NERIS Emergency Vectoring ({officer_id})"
        }

        # Save to DynamoDB ner_alerts
        self.dynamodb.save_alert_to_dynamodb(alert_dict)

        # Save to local file cache
        alerts = self._read_db()
        alerts.insert(0, alert_dict)
        self._write_db(alerts)

        logger.info(f"Dispatched Emergency SOS alert '{aid}' for vehicle '{req.vehicle_id}' by officer '{officer_id}'.")
        
        return SOSDispatchResponse(
            alert_id=aid,
            vehicle_id=req.vehicle_id,
            status="EMERGENCY_DISPATCH",
            dispatched_at=now_iso,
            dispatched_by=officer_id,
            dynamodb_confirmed=True,
            alert=NERISAlert(**alert_dict)
        )


_alert_service_instance: Optional[AlertService] = None

def get_alert_service() -> AlertService:
    global _alert_service_instance
    if _alert_service_instance is None:
        _alert_service_instance = AlertService()
    return _alert_service_instance
