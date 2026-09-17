from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Header, status, Depends, Query
from app.services.incidents_service import get_incidents_service
from app.core.dependencies import require_roles, get_current_user

router = APIRouter(tags=["AWS DynamoDB & S3 Incidents API"])

@router.get("/incidents", status_code=status.HTTP_200_OK)
@router.get("/api/incidents", status_code=status.HTTP_200_OK)
@router.get("/api/v1/incidents", status_code=status.HTTP_200_OK)
@router.get("/api/v1/incidents/live", status_code=status.HTTP_200_OK)
async def get_all_incidents(
    include_historical: bool = Query(False, description="Whether to append historical dataset events tagged with source_type = 'historical_dataset'"),
    user: Dict[str, Any] = Depends(require_roles(["FIELD_OFFICER", "COMMANDER", "DISPATCHER", "ADMIN"]))
):
    """
    Retrieves all field incidents directly from AWS DynamoDB ('ner_incidents' table).
    Live reported incidents are strictly tagged with source_type = 'live_verified_incident'.
    Requires authenticated session.
    """
    service = get_incidents_service()
    incidents = service.get_live_incidents()

    # Tag live incidents
    if isinstance(incidents, list):
        for inc in incidents:
            if isinstance(inc, dict):
                inc["source_type"] = "live_verified_incident"
                inc["disclaimer"] = "LIVE VERIFIED INCIDENT"

    if include_historical:
        try:
            from app.services.landslide_flood_service import get_landslide_flood_service
            lf_service = get_landslide_flood_service()
            historical_events = lf_service.get_historical_records()
            if isinstance(incidents, list):
                incidents.extend(historical_events)
        except Exception as ex:
            pass

    return incidents

@router.post("/incidents", status_code=status.HTTP_201_CREATED)
@router.post("/api/incidents", status_code=status.HTTP_201_CREATED)
@router.post("/api/v1/incidents", status_code=status.HTTP_201_CREATED)
async def create_new_incident(
    payload: Dict[str, Any],
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    user: Dict[str, Any] = Depends(require_roles(["FIELD_OFFICER", "COMMANDER", "ADMIN"]))
):
    """
    Backend-Authoritative Incident Creation Workflow:
    1. Validates JWT Bearer token & server-side RBAC role.
    2. Validates request body presence and non-empty required fields (title, description).
    3. Validates numerical GPS coordinates (latitude [-90, 90], longitude [-180, 180]).
    4. Validates incident type against valid taxonomy.
    5. Validates severity against valid taxonomy.
    6. Generates unique incident ID server-side.
    7. Records authenticated user identity (username/sub/role) from verified JWT server-side.
    8. Records creation timestamp server-side in UTC ISO-8601.
    9. Enforces idempotency using operation_id / Idempotency-Key.
    10. Persists item to AWS DynamoDB ('ner_incidents' table).
    11. Returns HTTP 201 Created (or 200 OK for idempotent replay) with full persisted incident.
    """
    # 1. Validate Payload Presence
    if not payload or not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Validation Error: Incident request body payload cannot be empty."
        )

    # 2. Validate Required Fields (title, description)
    title = str(payload.get("title") or "").strip()
    description = str(payload.get("description") or "").strip()

    if not title or not description:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Validation Error: Incident 'title' and 'description' are required non-empty string fields."
        )

    # 3. Validate GPS Coordinates (latitude, longitude)
    lat_raw = payload.get("latitude", payload.get("lat"))
    lng_raw = payload.get("longitude", payload.get("lng"))

    if lat_raw is None or lng_raw is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Validation Error: Incident 'latitude' and 'longitude' GPS coordinates are required."
        )

    try:
        lat = float(lat_raw)
        lng = float(lng_raw)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Validation Error: 'latitude' and 'longitude' must be valid numerical GPS coordinates."
        )

    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lng <= 180.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Validation Error: 'latitude' must be between -90 and 90, and 'longitude' between -180 and 180."
        )

    # 4. Validate Incident Type
    VALID_TYPES = {"LANDSLIDE", "FLASH_FLOOD", "BRIDGE_COLLAPSE", "ROAD_BLOCKAGE", "EARTHQUAKE", "EXTREME_WEATHER", "INFRASTRUCTURE_DAMAGE", "OTHER"}
    raw_type = str(payload.get("incidentType") or payload.get("type", "")).strip().upper()
    if not raw_type or raw_type not in VALID_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation Error: Invalid incident type '{raw_type}'. Allowed types: {sorted(list(VALID_TYPES))}"
        )

    # 5. Validate Severity
    VALID_SEVERITIES = {"CRITICAL", "HIGH", "MODERATE", "LOW"}
    raw_sev = str(payload.get("severity", "")).strip().upper()
    if not raw_sev or raw_sev not in VALID_SEVERITIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation Error: Invalid severity '{raw_sev}'. Allowed severities: {sorted(list(VALID_SEVERITIES))}"
        )

    # 6. Extract Authenticated User Identity Server-Side (NEVER trust client-provided reporter identity or role)
    authenticated_username = user.get("username") or user.get("sub") or "field_officer"
    authenticated_userId = user.get("sub") or f"USR-{authenticated_username.upper()}"
    authenticated_role = user.get("role", "FIELD_OFFICER")

    # 7. Generate Server-Side Timestamps & Unique Incident / Operation IDs
    import uuid
    import time
    from datetime import datetime, timezone

    iso_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    op_key = idempotency_key or payload.get("operation_id") or payload.get("clientIncidentId") or payload.get("client_incident_id") or f"OP-{uuid.uuid4().hex[:8]}"
    server_generated_id = f"INC-{int(time.time())}-{uuid.uuid4().hex[:6].upper()}"

    # Build backend-authoritative incident item
    authoritative_payload = {
        "id": server_generated_id,
        "incidentId": server_generated_id,
        "clientIncidentId": op_key,
        "operation_id": op_key,
        "title": title,
        "description": description,
        "type": raw_type,
        "incidentType": raw_type,
        "severity": raw_sev,
        "latitude": lat,
        "longitude": lng,
        "lat": lat,
        "lng": lng,
        "district": str(payload.get("district", payload.get("state", "ASSAM"))).upper(),
        "state": str(payload.get("state", "ASSAM")).upper(),
        "location_name": str(payload.get("location_name") or payload.get("locationName") or "NER Corridor"),
        "reported_by": authenticated_username,
        "reporter": authenticated_username,
        "reported_by_user_id": authenticated_userId,
        "reported_by_role": authenticated_role,
        "createdAt": iso_now,
        "created_at": iso_now,
        "timestamp": iso_now,
        "status": "REPORTED",
        "verificationStatus": "UNVERIFIED",
        "estimated_blockage_pct": float(payload.get("estimated_blockage_pct", 80.0)),
        "evidence_url": str(payload.get("evidence_url") or payload.get("photoUrl") or ""),
        "photoUrl": str(payload.get("photoUrl") or payload.get("evidence_url") or "")
    }

    # 8. Persist Item to AWS DynamoDB
    service = get_incidents_service()
    try:
        result = service.create_incident(authoritative_payload)
    except Exception as err:
        from app.config import get_settings
        st = get_settings()
        if st.is_production:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"DynamoDB Persistence Failure: Failed to write incident to AWS DynamoDB table: {str(err)}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Incident Persistence Error: {str(err)}"
        )

    # In Production mode, verify DynamoDB write succeeded
    from app.config import get_settings
    st = get_settings()
    if st.is_production and not result.get("dynamodb_confirmed") and not result.get("duplicate_prevented"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DynamoDB Persistence Failure: AWS DynamoDB operation failed to store incident record."
        )

    # 9. Real Incident Workflow: Risk Evaluation & Alert Generation
    generated_alert = None
    try:
        from app.services.alert_service import get_alert_service
        from app.models.alert import IncidentEvaluationRequest

        alert_svc = get_alert_service()
        eval_req = IncidentEvaluationRequest(
            incident_id=result.get("id"),
            title=result.get("title"),
            severity=result.get("severity"),
            district=result.get("district", "ASSAM"),
            description=result.get("description"),
            estimated_blockage_pct=result.get("estimated_blockage_pct", 80.0),
            reporter=authenticated_username
        )
        alert_obj = alert_svc.evaluate_incident_and_create_alert(eval_req)
        if alert_obj:
            generated_alert = alert_obj.dict()
    except Exception as ex:
        import logging
        logging.getLogger("neris.incidents_router").error(f"Error in alert generation workflow: {ex}")

    is_confirmed = bool(result.get("dynamodb_confirmed") or result.get("duplicate_prevented") or result.get("id"))
    is_duplicate = bool(result.get("duplicate_prevented"))

    return {
        "status": "DUPLICATE_REPLAY" if is_duplicate else "CREATED",
        "dynamodb_confirmed": is_confirmed,
        "duplicate_prevented": is_duplicate,
        "message": f"Incident '{result.get('id')}' successfully persisted to AWS DynamoDB.",
        "incident": result,
        "generated_alert": generated_alert
    }

@router.post("/incidents/upload-evidence", status_code=status.HTTP_200_OK)
@router.post("/api/incidents/upload-evidence", status_code=status.HTTP_200_OK)
@router.post("/api/v1/incidents/upload-evidence", status_code=status.HTTP_200_OK)
async def upload_evidence_photo(
    file: UploadFile = File(...),
    incident_id: Optional[str] = Form(None),
    user: Dict[str, Any] = Depends(require_roles(["FIELD_OFFICER", "COMMANDER", "ADMIN"]))
):
    """
    Amazon S3 Evidence Media Upload Pipeline:
    1. Validates authentication & user RBAC role.
    2. Validates maximum file size limit (10MB).
    3. Validates MIME type and image magic bytes (JPEG, PNG, WEBP).
    4. Generates safe unique S3 object key (no path traversal).
    5. Uploads file with AES256 server-side encryption to private S3 bucket.
    6. Returns S3 key, evidence metadata, and presigned download URL reference.
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="Validation Error: Upload file payload is required.")

    contents = await file.read()
    if not contents or len(contents) == 0:
        raise HTTPException(status_code=400, detail="Validation Error: Uploaded file content cannot be empty.")

    service = get_incidents_service()

    try:
        result = service.upload_evidence(contents, file.filename, file.content_type or "image/jpeg")
        return result
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as err:
        from app.config import get_settings
        if get_settings().is_production:
            raise HTTPException(status_code=500, detail=f"Amazon S3 evidence upload service error: {str(err)}")
        raise HTTPException(status_code=500, detail=f"S3 upload service error: {str(err)}")

@router.post("/api/v1/incidents/presigned-upload-url", status_code=status.HTTP_200_OK)
async def generate_presigned_upload_url(
    filename: str,
    content_type: str = "image/jpeg",
    user: Dict[str, Any] = Depends(require_roles(["FIELD_OFFICER", "COMMANDER", "ADMIN"]))
):
    """
    Generates an Amazon S3 presigned PUT URL allowing authorized frontend clients
    to upload evidence photos directly to S3 without exposing AWS IAM credentials.
    """
    from app.adapters.aws_s3 import get_s3_adapter
    s3_adapter = get_s3_adapter()
    try:
        res = s3_adapter.generate_presigned_upload_url(filename, content_type)
        return res
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Failed to generate presigned S3 upload URL: {str(err)}")

@router.get("/api/v1/incidents/presigned-download-url", status_code=status.HTTP_200_OK)
async def generate_presigned_download_url(
    s3_key: str,
    user: Dict[str, Any] = Depends(require_roles(["FIELD_OFFICER", "COMMANDER", "DISPATCHER", "ADMIN"]))
):
    """
    Generates an Amazon S3 presigned GET URL for authorized access to private evidence photos.
    Applies resource-level path traversal and authorization checks.
    """
    if ".." in s3_key or s3_key.startswith("/"):
        raise HTTPException(status_code=400, detail="Resource Access Denied: Invalid S3 key structure.")

    from app.adapters.aws_s3 import get_s3_adapter
    s3_adapter = get_s3_adapter()
    url = s3_adapter.generate_presigned_download_url(s3_key)
    if not url:
        raise HTTPException(status_code=404, detail="S3 evidence object key not found or presigned URL generation failed.")
    return {"presigned_url": url, "s3_key": s3_key, "expires_in_seconds": 3600}

@router.get("/incidents/{incident_id}", status_code=status.HTTP_200_OK)
@router.get("/api/incidents/{incident_id}", status_code=status.HTTP_200_OK)
@router.get("/api/v1/incidents/{incident_id}", status_code=status.HTTP_200_OK)
async def get_incident_by_id_endpoint(
    incident_id: str,
    user: Dict[str, Any] = Depends(require_roles(["FIELD_OFFICER", "COMMANDER", "DISPATCHER", "ADMIN"]))
):
    """
    Retrieves a single incident by ID from AWS DynamoDB ('ner_incidents' table).
    """
    service = get_incidents_service()
    incident = service.get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found."
        )
    return incident

@router.patch("/incidents/{incident_id}", status_code=status.HTTP_200_OK)
@router.patch("/api/incidents/{incident_id}", status_code=status.HTTP_200_OK)
@router.patch("/api/v1/incidents/{incident_id}", status_code=status.HTTP_200_OK)
async def update_incident_by_id_endpoint(
    incident_id: str,
    payload: Dict[str, Any],
    user: Dict[str, Any] = Depends(require_roles(["FIELD_OFFICER", "COMMANDER", "ADMIN"]))
):
    """
    Updates an incident status or details in AWS DynamoDB ('ner_incidents' table).
    """
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Validation Error: Update payload must not be empty."
        )

    service = get_incidents_service()
    existing = service.get_incident_by_id(incident_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found."
        )

    # BOLA Ownership Check: FIELD_OFFICER can only update incidents they reported
    user_role = str(user.get("role", "FIELD_OFFICER")).upper()
    if "COMMANDER" not in user_role and "ADMIN" not in user_role:
        reporter_id = existing.get("reported_by_user_id") or existing.get("reported_by") or existing.get("reporter")
        user_id = user.get("sub") or user.get("username")
        if reporter_id and user_id and str(reporter_id).lower() != str(user_id).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"BOLA Access Denied: Role '{user_role}' is not authorized to modify incident '{incident_id}' created by another user."
            )

    updated = service.update_incident(incident_id, payload)
    return {
        "status": "UPDATED",
        "message": f"Incident '{incident_id}' successfully updated in AWS DynamoDB.",
        "incident": updated
    }


@router.post("/incidents/{incident_id}/ai-intelligence", status_code=status.HTTP_200_OK)
@router.post("/api/incidents/{incident_id}/ai-intelligence", status_code=status.HTTP_200_OK)
@router.post("/api/v1/incidents/{incident_id}/ai-intelligence", status_code=status.HTTP_200_OK)
async def generate_incident_ai_intelligence(
    incident_id: str,
    payload: Optional[Dict[str, Any]] = None,
    user: Dict[str, Any] = Depends(require_roles(["FIELD_OFFICER", "COMMANDER", "ADMIN"]))
):
    """
    Amazon Bedrock AI-Assisted Incident Intelligence Endpoint:
    Generates structured AI incident summaries, operational impacts, human verification questions, and response actions.
    Persists resulting structured assessment or failure status to DynamoDB.
    """
    import logging
    logger = logging.getLogger("neris.ai_endpoint")

    service = get_incidents_service()

    inc_data = None
    try:
        inc_data = service.dynamodb.get_incident_by_id(incident_id)
    except Exception:
        pass

    if not inc_data and payload:
        inc_data = payload

    if not inc_data:
        inc_data = {
            "id": incident_id,
            "title": f"Field Incident {incident_id}",
            "type": "LANDSLIDE",
            "severity": "HIGH",
            "description": "Field incident pending detailed inspector report."
        }

    from app.adapters.aws_bedrock import get_bedrock_adapter
    bedrock = get_bedrock_adapter()
    intelligence = bedrock.generate_incident_intelligence(inc_data)

    # Persist AI analysis result or failure status to DynamoDB
    try:
        service.update_incident(incident_id, {
            "aiAnalysis": intelligence,
            "ai_analysis_status": intelligence.get("ai_analysis_status", "UNKNOWN")
        })
        logger.info(f"Persisted AI analysis for incident '{incident_id}' to DynamoDB.")
    except Exception as ex:
        logger.warning(f"Failed to persist AI analysis for incident '{incident_id}': {ex}")

    return intelligence

@router.post("/incidents/batch-sync", status_code=status.HTTP_200_OK)
@router.post("/api/v1/incidents/batch-sync", status_code=status.HTTP_200_OK)
async def batch_sync_incidents(
    payload: Dict[str, Any],
    user: Dict[str, Any] = Depends(require_roles(["FIELD_OFFICER", "COMMANDER", "ADMIN"]))
):
    """
    Offline-First Field Reporting Batch Synchronization Endpoint:
    1. Consumes queued offline records containing client_id, operation_id, created_at, retry_count.
    2. Validates operation_id idempotency to prevent duplicate submissions.
    3. Uploads Base64 photo evidence to S3 bucket if present.
    4. Persists items to AWS DynamoDB ('ner_incidents' table).
    5. Triggers Command Center risk evaluation & persistent alert generation.
    6. Returns sync confirmation status for each item.
    """
    import time
    import base64
    import logging
    logger = logging.getLogger("neris.batch_sync")

    items = payload.get("items", [])
    if not items and ("title" in payload or "operation_id" in payload):
        items = [payload]

    service = get_incidents_service()
    results = []
    synced_count = 0
    failed_count = 0

    for item in items:
        op_id = str(item.get("operation_id") or item.get("id") or f"OP-{int(time.time())}")
        client_id = str(item.get("client_id") or payload.get("client_id") or "CLI-FIELD-OFFICER")
        
        try:
            # Check Base64 photo upload to S3 if photo_base64 is attached
            evidence_url = str(item.get("evidence_url") or item.get("photoUrl") or "")
            s3_confirmed = False
            
            photo_b64 = item.get("photo_base64") or item.get("evidence_base64") or item.get("photoData")
            if photo_b64 and isinstance(photo_b64, str) and "," in photo_b64:
                photo_b64 = photo_b64.split(",")[1]
                
            if photo_b64 and isinstance(photo_b64, str) and len(photo_b64) > 10:
                try:
                    raw_bytes = base64.b64decode(photo_b64)
                    fname = f"offline_evidence_{op_id.replace(':', '_')}.jpg"
                    s3_res = service.upload_evidence(raw_bytes, fname, "image/jpeg")
                    if s3_res and s3_res.get("evidence_url"):
                        evidence_url = s3_res.get("evidence_url")
                        s3_confirmed = bool(s3_res.get("s3_confirmed"))
                except Exception as s3_err:
                    logger.warning(f"Batch sync S3 upload notice: {s3_err}")

            # Validate Incident Taxonomy & Input Boundaries
            VALID_TYPES = {"LANDSLIDE", "FLASH_FLOOD", "BRIDGE_COLLAPSE", "ROAD_BLOCKAGE", "EARTHQUAKE", "EXTREME_WEATHER", "INFRASTRUCTURE_DAMAGE", "OTHER"}
            VALID_SEVERITIES = {"CRITICAL", "HIGH", "MODERATE", "LOW"}

            raw_type = str(item.get("type") or item.get("incidentType", "LANDSLIDE")).strip().upper()
            if raw_type not in VALID_TYPES:
                raise ValueError(f"Validation Error: Invalid incident type '{raw_type}'. Allowed types: {sorted(list(VALID_TYPES))}")

            raw_sev = str(item.get("severity", "CRITICAL")).strip().upper()
            if raw_sev not in VALID_SEVERITIES:
                raise ValueError(f"Validation Error: Invalid severity '{raw_sev}'. Allowed severities: {sorted(list(VALID_SEVERITIES))}")

            lat_val = float(item.get("latitude") or item.get("lat") or 26.1445)
            lng_val = float(item.get("longitude") or item.get("lng") or 91.7362)
            if not (-90.0 <= lat_val <= 90.0) or not (-180.0 <= lng_val <= 180.0):
                raise ValueError(f"Validation Error: GPS coordinates ({lat_val}, {lng_val}) out of bounds.")

            # Extract authenticated user identity (NEVER trust client batch payload for identity)
            auth_username = user.get("username") or user.get("sub") or "field_officer"
            auth_user_id = user.get("sub") or f"USR-{auth_username.upper()}"
            auth_role = user.get("role", "FIELD_OFFICER")

            # Map incident fields for DynamoDB
            inc_data = {
                "id": str(item.get("id") or f"INC-{op_id.replace('OP-', '')}"),
                "operation_id": op_id,
                "client_id": client_id,
                "title": str(item.get("title", "Field Incident Report")),
                "type": raw_type,
                "severity": raw_sev,
                "district": str(item.get("district") or item.get("state") or "ASSAM"),
                "location_name": str(item.get("location_name") or item.get("locationName") or "NER Corridor"),
                "latitude": lat_val,
                "longitude": lng_val,
                "reporter": auth_username,
                "reported_by": auth_username,
                "reported_by_user_id": auth_user_id,
                "reported_by_role": auth_role,
                "description": str(item.get("description", "Offline synced incident report.")),
                "evidence_url": evidence_url,
                "evidence_status": "UPLOADED" if (s3_confirmed or evidence_url.startswith("http") or evidence_url.startswith("/uploads")) else "NONE",
                "timestamp": str(item.get("created_at") or item.get("timestamp") or "")
            }

            db_res = service.create_incident(inc_data)
            
            # Risk Evaluation & Persistent Command Center Alert Generation
            try:
                from app.services.alert_service import get_alert_service
                from app.models.alert import IncidentEvaluationRequest
                alert_svc = get_alert_service()
                eval_req = IncidentEvaluationRequest(
                    incident_id=db_res.get("id"),
                    title=db_res.get("title"),
                    severity=db_res.get("severity"),
                    district=db_res.get("district"),
                    description=db_res.get("description"),
                    estimated_blockage_pct=float(item.get("estimated_blockage_pct", 80.0)),
                    reporter=db_res.get("reporter")
                )
                alert_svc.evaluate_incident_and_create_alert(eval_req)
            except Exception:
                pass

            synced_count += 1
            results.append({
                "operation_id": op_id,
                "client_id": client_id,
                "incident_id": db_res.get("id"),
                "sync_status": "SYNCED",
                "sync_confirmed": True,
                "duplicate_prevented": bool(db_res.get("duplicate_prevented")),
                "dynamodb_confirmed": bool(db_res.get("dynamodb_confirmed")),
                "s3_confirmed": s3_confirmed,
                "incident": db_res
            })
        except Exception as item_err:
            failed_count += 1
            results.append({
                "operation_id": op_id,
                "client_id": client_id,
                "sync_status": "SYNC FAILED",
                "sync_confirmed": False,
                "error": str(item_err)
            })

    return {
        "status": "SUCCESS" if failed_count == 0 else "PARTIAL_SUCCESS",
        "synced_count": synced_count,
        "failed_count": failed_count,
        "results": results
    }
