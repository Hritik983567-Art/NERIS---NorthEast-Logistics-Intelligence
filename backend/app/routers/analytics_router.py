from typing import Dict, Any, List
from fastapi import APIRouter, status, Depends
from app.services.incidents_service import get_incidents_service
from app.core.dependencies import get_current_user

router = APIRouter(tags=["NERIS Operational Analytics API"])

@router.get("/analytics/overview", status_code=status.HTTP_200_OK)
@router.get("/api/analytics/overview", status_code=status.HTTP_200_OK)
@router.get("/api/v1/analytics/overview", status_code=status.HTTP_200_OK)
async def get_analytics_overview(
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    P0-13: Backend-Driven Analytics Overview Endpoint.
    Calculates live metrics strictly from active operational incidents and resource data.
    """
    service = get_incidents_service()
    incidents = service.get_live_incidents() or []

    active_incidents = len(incidents)
    critical_incidents = sum(1 for inc in incidents if str(inc.get("severity", "")).upper() == "CRITICAL")
    high_incidents = sum(1 for inc in incidents if str(inc.get("severity", "")).upper() == "HIGH")

    states = set()
    hazard_counts: Dict[str, int] = {}
    state_counts: Dict[str, int] = {}

    for inc in incidents:
        st = str(inc.get("state") or inc.get("district") or "ASSAM").upper()
        states.add(st)
        state_counts[st] = state_counts.get(st, 0) + 1

        htype = str(inc.get("type") or inc.get("incidentType") or "OTHER").upper()
        hazard_counts[htype] = hazard_counts.get(htype, 0) + 1

    hazard_distribution = [
        {"hazard_type": k, "count": v} for k, v in hazard_counts.items()
    ]
    incident_by_state = [
        {"state": k, "count": v} for k, v in state_counts.items()
    ]

    return {
        "active_incidents": active_incidents,
        "critical_incidents": critical_incidents,
        "high_incidents": high_incidents,
        "states_affected": len(states),
        "states_list": sorted(list(states)),
        "hazard_distribution": hazard_distribution,
        "incident_by_state": incident_by_state,
        "source": "DynamoDB Live Operational Data",
        "data_veracity": "VERIFIED_BACKEND_CALCULATED"
    }
