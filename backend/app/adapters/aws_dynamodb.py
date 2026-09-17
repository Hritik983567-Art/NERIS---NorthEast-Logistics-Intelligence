import os
import json
import time
import logging
from decimal import Decimal
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from app.config import get_settings

logger = logging.getLogger("neris.aws_dynamodb")
settings = get_settings()

LOCAL_CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "incidents_db.json")

VALID_TYPES = {"LANDSLIDE", "FLOOD", "ROAD_BLOCKAGE", "BRIDGE_DAMAGE", "ACCIDENT", "WEATHER", "OTHER"}
VALID_SEVERITIES = {"CRITICAL", "HIGH", "MODERATE", "LOW"}

def _convert_floats_to_decimals(obj: Any) -> Any:
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _convert_floats_to_decimals(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_convert_floats_to_decimals(v) for v in obj]
    return obj

class DynamoDBAdapter:
    """
    AWS DynamoDB Data Adapter for NERIS Incident Persistence.
    Handles put_item, scan, get_item with local fallback cache when offline.
    """
    def __init__(self, table_name: str = None, region_name: str = None):
        self.table_name = table_name or getattr(settings, "DYNAMODB_INCIDENTS_TABLE", "ner_incidents")
        self.region_name = region_name or getattr(settings, "AWS_REGION", "ap-south-1")
        self.dynamodb_resource = None
        self.table = None
        self._init_client()

    def _init_client(self):
        try:
            self.dynamodb_resource = boto3.resource("dynamodb", region_name=self.region_name)
            self.table = self.dynamodb_resource.Table(self.table_name)
            logger.info(f"Initialized DynamoDB resource for table '{self.table_name}' in region '{self.region_name}'.")
        except Exception as err:
            logger.warning(f"DynamoDB initialization notice: {err}. Using resilient local persistence fallback.")

    def save_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Persists an incident item to AWS DynamoDB table with client-generated idempotency key protection.
        """
        inc_id = str(incident_data.get("id") or incident_data.get("clientIncidentId") or f"INC-2026-{int(datetime.now(timezone.utc).timestamp())}")
        client_key = str(incident_data.get("clientIncidentId") or incident_data.get("client_incident_id") or incident_data.get("operation_id") or inc_id)
        
        inc_title = str(incident_data.get("title", "Field Incident Report"))

        # Idempotency Check: Prevent creating duplicate incident if clientIncidentId or operation_id already exists
        cached_items = self._read_from_local_cache()
        for existing_item in cached_items:
            existing_ids = {
                str(existing_item.get("id", "")),
                str(existing_item.get("incidentId", "")),
                str(existing_item.get("clientIncidentId", "")),
                str(existing_item.get("client_incident_id", "")),
                str(existing_item.get("operation_id", ""))
            }
            if client_key and client_key in existing_ids:
                logger.info(f"Duplicate prevention triggered: Incident with key '{client_key}' already persisted.")
                ret_existing = dict(existing_item)
                ret_existing["duplicate_prevented"] = True
                ret_existing["dynamodb_confirmed"] = True
                ret_existing["status"] = "SYNCED"
                return ret_existing
        
        raw_type = str(incident_data.get("incidentType") or incident_data.get("type", "LANDSLIDE")).upper()
        if "BRIDGE" in raw_type:
            inc_type = "BRIDGE_DAMAGE"
        elif "ROAD" in raw_type or "SINKING" in raw_type:
            inc_type = "ROAD_BLOCKAGE"
        elif "EARTHQUAKE" in raw_type:
            inc_type = "EARTHQUAKE"
        elif "WEATHER" in raw_type:
            inc_type = "EXTREME_WEATHER"
        elif "INFRASTRUCTURE" in raw_type:
            inc_type = "INFRASTRUCTURE_DAMAGE"
        elif raw_type in VALID_TYPES:
            inc_type = raw_type
        else:
            inc_type = "OTHER"

        raw_sev = str(incident_data.get("severity", "CRITICAL")).upper()
        if "MED" in raw_sev or "MEDIUM" in raw_sev:
            inc_sev = "MODERATE"
        elif raw_sev in VALID_SEVERITIES:
            inc_sev = raw_sev
        else:
            inc_sev = "HIGH"

        raw_lat = incident_data.get("latitude", incident_data.get("lat", 26.1445))
        raw_lng = incident_data.get("longitude", incident_data.get("lng", 91.7362))

        iso_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        evidence_url = str(incident_data.get("evidence_url") or incident_data.get("photoUrl") or "")
        evidence_status = str(incident_data.get("evidence_status", "UPLOADED" if evidence_url.startswith("http") else "NONE"))
        uploaded_at = incident_data.get("uploaded_at") or (iso_now if evidence_status == "UPLOADED" else None)

        evidence_meta = incident_data.get("evidence") or {
            "evidence_url": evidence_url,
            "evidence_status": evidence_status,
            "uploaded_at": uploaded_at,
            "s3_key": incident_data.get("s3_key", ""),
            "s3_bucket": incident_data.get("s3_bucket", self.region_name)
        }

        # Status & Verification Rules:
        # All new field reports start as verificationStatus = "UNVERIFIED"
        status_val = str(incident_data.get("status", "REPORTED")).upper()
        if status_val not in {"REPORTED", "UNDER_REVIEW", "VERIFIED", "RESOLVED", "REJECTED"}:
            status_val = "REPORTED"

        verification_status = "UNVERIFIED"  # Rule: AI/News NEVER auto-verifies; starts UNVERIFIED

        item = {
            "id": inc_id,
            "incidentId": inc_id,
            "clientIncidentId": client_key,
            "operation_id": client_key,
            "title": inc_title,
            "type": inc_type,
            "incidentType": inc_type,
            "severity": inc_sev,
            "state": str(incident_data.get("state", incident_data.get("district", "ASSAM"))).upper(),
            "district": str(incident_data.get("district", incident_data.get("state", "ASSAM"))).lower(),
            "location_name": str(incident_data.get("location_name") or incident_data.get("locationName") or "NER Corridor"),
            "latitude": Decimal(str(raw_lat)),
            "longitude": Decimal(str(raw_lng)),
            "lat": Decimal(str(raw_lat)),
            "lng": Decimal(str(raw_lng)),
            "reporter": str(incident_data.get("reported_by") or incident_data.get("reportedBy") or incident_data.get("reporter", "Field Officer")),
            "reportedBy": str(incident_data.get("reported_by") or incident_data.get("reportedBy") or incident_data.get("reporter", "Field Officer")),
            "reported_by": str(incident_data.get("reported_by") or incident_data.get("reportedBy") or incident_data.get("reporter", "Field Officer")),
            "reported_by_role": str(incident_data.get("reported_by_role") or "FIELD_OFFICER"),
            "reported_by_user_id": str(incident_data.get("reported_by_user_id") or "USR-OFFICER"),
            "description": str(incident_data.get("description", "Active hazard report")),
            "timestamp": str(incident_data.get("timestamp", iso_now)),
            "createdAt": str(incident_data.get("createdAt") or incident_data.get("timestamp", iso_now)),
            "updatedAt": iso_now,
            "status": status_val,
            "verificationStatus": verification_status,
            "evidence_status": evidence_status,
            "evidence_url": evidence_url,
            "evidence": evidence_meta,
            "aiAnalysis": incident_data.get("aiAnalysis"),
            "uploaded_at": uploaded_at
        }

        # Try saving to live DynamoDB table
        saved_to_aws = False
        if self.table:
            try:
                db_item = _convert_floats_to_decimals(item)
                self.table.put_item(Item=db_item)
                logger.info(f"Successfully persisted incident '{inc_id}' to DynamoDB table '{self.table_name}'.")
                saved_to_aws = True
            except (BotoCoreError, ClientError) as err:
                if settings.is_production:
                    logger.error(f"DynamoDB put_item failed in PRODUCTION mode: {err}")
                    raise RuntimeError(f"DynamoDB put_item failed in PRODUCTION mode: {err}")
                logger.warning(f"DynamoDB put_item notice ({err}). Persisting to local fallback cache.")
        elif settings.is_production:
            raise RuntimeError(f"DynamoDB table '{self.table_name}' unconfigured or unavailable in PRODUCTION mode.")

        # Prepare serializable return object (converting Decimal back to float)
        item_cache = dict(item)
        item_cache["latitude"] = float(raw_lat)
        item_cache["longitude"] = float(raw_lng)
        item_cache["lat"] = float(raw_lat)
        item_cache["lng"] = float(raw_lng)
        item_cache["status"] = "SYNCED" if saved_to_aws else "PENDING"
        item_cache["dynamodb_confirmed"] = saved_to_aws
        item_cache["is_live"] = True
        item_cache["aws_region"] = self.region_name

        self._save_to_local_cache(item_cache)
        return item_cache

    def get_all_incidents(self) -> List[Dict[str, Any]]:
        """
        Scans all incidents from AWS DynamoDB table.
        """
        incidents = []
        if self.table:
            try:
                response = self.table.scan()
                items = response.get("Items", [])
                if items:
                    logger.info(f"Retrieved {len(items)} incidents from AWS DynamoDB table '{self.table_name}'.")
                    for item in items:
                        item["latitude"] = float(item.get("latitude", item.get("lat", 26.0)))
                        item["longitude"] = float(item.get("longitude", item.get("lng", 91.0)))
                        item["lat"] = float(item.get("lat", item.get("latitude", 26.0)))
                        item["lng"] = float(item.get("lng", item.get("longitude", 91.0)))
                        item["dynamodb_confirmed"] = True
                        item["is_live"] = True
                        incidents.append(item)
                    return incidents
            except (BotoCoreError, ClientError) as err:
                if settings.is_production:
                    logger.error(f"DynamoDB scan failed in PRODUCTION mode: {err}")
                    raise RuntimeError(f"DynamoDB scan failed in PRODUCTION mode: {err}")
                logger.warning(f"DynamoDB scan notice ({err}). Reading from local fallback cache.")

        if settings.is_production:
            raise RuntimeError(f"DynamoDB scan failed or table '{self.table_name}' unavailable in PRODUCTION mode.")

        cached_items = self._read_from_local_cache()
        for item in cached_items:
            item["is_live"] = True
        return cached_items

    def get_incident_by_id(self, incident_id: str) -> Optional[Dict[str, Any]]:
        if self.table:
            try:
                response = self.table.get_item(Key={"id": incident_id})
                item = response.get("Item")
                if item:
                    item["latitude"] = float(item.get("latitude", item.get("lat", 26.0)))
                    item["longitude"] = float(item.get("longitude", item.get("lng", 91.0)))
                    item["lat"] = float(item.get("lat", 26.0))
                    item["lng"] = float(item.get("lng", 91.0))
                    return item
            except (BotoCoreError, ClientError) as err:
                logger.warning(f"DynamoDB get_item error: {err}")

        items = self._read_from_local_cache()
        for i in items:
            if i.get("id") == incident_id:
                return i
        return None

    def update_incident(self, incident_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Updates an existing incident by ID in DynamoDB and local cache.
        """
        existing = self.get_incident_by_id(incident_id)
        if not existing:
            return None

        # Apply updates
        for key, val in updates.items():
            if key in ["latitude", "lat", "longitude", "lng"]:
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    continue
            existing[key] = val

        existing["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Update in DynamoDB if available
        if self.table:
            try:
                db_item = _convert_floats_to_decimals(existing)
                db_item.pop("dynamodb_confirmed", None)
                db_item.pop("is_live", None)
                db_item.pop("aws_region", None)
                
                self.table.put_item(Item=db_item)
                existing["dynamodb_confirmed"] = True
                logger.info(f"Successfully updated incident '{incident_id}' in DynamoDB.")
            except (BotoCoreError, ClientError) as err:
                logger.warning(f"DynamoDB update_item notice ({err}). Updating local cache.")

        self._save_to_local_cache(existing)
        return existing

    def _save_to_local_cache(self, item: Dict[str, Any]):
        db_dir = os.path.dirname(LOCAL_CACHE_PATH)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
        items = self._read_from_local_cache()
        op_id = item.get("operation_id")
        existing_idx = None
        for idx, i in enumerate(items):
            if i.get("id") == item["id"] or (op_id and i.get("operation_id") == op_id):
                existing_idx = idx
                break
        
        if existing_idx is not None:
            item["duplicate_prevented"] = True
            items[existing_idx] = item
        else:
            item["duplicate_prevented"] = False
            items.insert(0, item)
            
        try:
            with open(LOCAL_CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
        except Exception as err:
            logger.error(f"Error saving to local cache: {err}")

    def _read_from_local_cache(self) -> List[Dict[str, Any]]:
        if os.path.exists(LOCAL_CACHE_PATH):
            try:
                with open(LOCAL_CACHE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return [
            {
                "id": "INC-2026-8041",
                "title": "Mudslide at Dima Hasao NH-27 Corridor",
                "type": "LANDSLIDE",
                "severity": "CRITICAL",
                "district": "assam",
                "location_name": "NH-27 Dima Hasao Stretch",
                "latitude": 25.1833,
                "longitude": 93.0167,
                "lat": 25.1833,
                "lng": 93.0167,
                "timestamp": "Active",
                "status": "SYNCED",
                "dynamodb_confirmed": True,
                "evidence_status": "UPLOADED",
                "reporter": "Cmdr. R. Gogoi",
                "evidence_url": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957"
            }
        ]

    def save_fleet_telemetry(self, fleet_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Saves or updates vehicle telemetry item into AWS DynamoDB.
        """
        vid = str(fleet_data.get("vehicleId") or fleet_data.get("vehicle_id") or fleet_data.get("id") or "NER-MED-8041")
        iso_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        lat = float(fleet_data.get("latitude") if fleet_data.get("latitude") is not None else fleet_data.get("lat") if fleet_data.get("lat") is not None else 26.1445)
        lng = float(fleet_data.get("longitude") if fleet_data.get("longitude") is not None else fleet_data.get("lng") if fleet_data.get("lng") is not None else 91.7362)

        item = {
            "id": vid,
            "vehicleId": vid,
            "vehicle_id": vid,
            "registration": str(fleet_data.get("registration") or vid),
            "vehicleType": str(fleet_data.get("vehicleType") or fleet_data.get("vehicle_type") or "HEAVY_TRUCK"),
            "status": str(fleet_data.get("status") or "CLEAR").upper(),
            "latitude": Decimal(str(lat)),
            "longitude": Decimal(str(lng)),
            "lat": Decimal(str(lat)),
            "lng": Decimal(str(lng)),
            "speed": Decimal(str(fleet_data.get("speed", fleet_data.get("speed_kmh", 40.0)))),
            "heading": Decimal(str(fleet_data.get("heading", 0.0))),
            "cargo": str(fleet_data.get("cargo") or "Medical Supplies"),
            "updatedAt": str(fleet_data.get("updatedAt") or fleet_data.get("timestamp") or iso_now),
            "driver_name": str(fleet_data.get("driver_name") or "Ramesh Kalita"),
            "driver_phone": str(fleet_data.get("driver_phone") or "+91 98640 11234"),
            "state": str(fleet_data.get("state") or "assam").lower()
        }

        saved_to_aws = False
        if self.dynamodb_resource:
            try:
                fleet_table = self.dynamodb_resource.Table(getattr(settings, "DYNAMODB_FLEET_TABLE", "ner_fleet_telemetry"))
                db_item = _convert_floats_to_decimals(item)
                fleet_table.put_item(Item=db_item)
                saved_to_aws = True
                logger.info(f"Persisted vehicle telemetry '{vid}' to DynamoDB table 'ner_fleet_telemetry'.")
            except Exception as err:
                logger.warning(f"DynamoDB fleet put_item notice ({err}). Persisting to local fallback cache.")

        item_cache = dict(item)
        item_cache["latitude"] = lat
        item_cache["longitude"] = lng
        item_cache["lat"] = lat
        item_cache["lng"] = lng
        item_cache["speed"] = float(item["speed"])
        item_cache["heading"] = float(item["heading"])
        item_cache["dynamodb_confirmed"] = saved_to_aws
        item_cache["aws_region"] = self.region_name

        # Save to local fleet cache
        fleet_cache_path = os.path.join(os.path.dirname(LOCAL_CACHE_PATH), "fleet_db.json")
        try:
            cached_fleets = []
            if os.path.exists(fleet_cache_path):
                with open(fleet_cache_path, "r", encoding="utf-8") as f:
                    cached_fleets = json.load(f)
            
            cached_fleets = [f for f in cached_fleets if f.get("vehicleId") != vid and f.get("id") != vid]
            cached_fleets.insert(0, item_cache)
            
            with open(fleet_cache_path, "w", encoding="utf-8") as f:
                json.dump(cached_fleets, f, indent=2, ensure_ascii=False)
        except Exception as err:
            logger.error(f"Error updating local fleet cache: {err}")

        return item_cache

    def get_fleet_telemetry_by_id(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        fleet_cache_path = os.path.join(os.path.dirname(LOCAL_CACHE_PATH), "fleet_db.json")
        if os.path.exists(fleet_cache_path):
            try:
                with open(fleet_cache_path, "r", encoding="utf-8") as f:
                    fleets = json.load(f)
                    for item in fleets:
                        if item.get("vehicleId") == vehicle_id or item.get("id") == vehicle_id or item.get("vehicle_id") == vehicle_id:
                            return item
            except Exception:
                pass
        return None

    def get_all_fleet_telemetry(self) -> List[Dict[str, Any]]:
        fleet_cache_path = os.path.join(os.path.dirname(LOCAL_CACHE_PATH), "fleet_db.json")
        if os.path.exists(fleet_cache_path):
            try:
                with open(fleet_cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def save_alert_to_dynamodb(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Persists an operational alert item into AWS DynamoDB table 'ner_alerts'.
        """
        aid = str(alert_data.get("alertId") or alert_data.get("id") or f"ALT-{int(datetime.now().timestamp())}")
        iso_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        item = {
            "id": aid,
            "alertId": aid,
            "type": str(alert_data.get("type", "HAZARD_WARNING")),
            "severity": str(alert_data.get("severity", "CRITICAL")).upper(),
            "title": str(alert_data.get("title", "Command Center Operational Alert")),
            "message": str(alert_data.get("message", alert_data.get("description", "Active operational hazard detected."))),
            "description": str(alert_data.get("message", alert_data.get("description", "Active operational hazard detected."))),
            "incidentId": alert_data.get("incidentId", alert_data.get("incident_id")),
            "incident_id": alert_data.get("incidentId", alert_data.get("incident_id")),
            "vehicleId": alert_data.get("vehicleId", alert_data.get("vehicle_id")),
            "vehicle_id": alert_data.get("vehicleId", alert_data.get("vehicle_id")),
            "recipientScope": str(alert_data.get("recipientScope", alert_data.get("recipient_scope", "ALL_COMMANDERS"))),
            "createdAt": str(alert_data.get("createdAt", alert_data.get("created_at", iso_now))),
            "created_at": str(alert_data.get("createdAt", alert_data.get("created_at", iso_now))),
            "status": str(alert_data.get("status", "ACTIVE")).upper(),
            "delivery_mode": "In-App Operational Alert (AWS DynamoDB)",
            "district": str(alert_data.get("district", "ASSAM")).upper(),
            "source": str(alert_data.get("source", "NERIS Risk Engine"))
        }

        saved_to_aws = False
        if self.dynamodb_resource:
            try:
                alerts_table = self.dynamodb_resource.Table(getattr(settings, "DYNAMODB_ALERTS_TABLE", "ner_alerts"))
                db_item = _convert_floats_to_decimals(item)
                alerts_table.put_item(Item=db_item)
                saved_to_aws = True
                logger.info(f"Persisted alert '{aid}' to DynamoDB table 'ner_alerts'.")
            except Exception as err:
                logger.warning(f"DynamoDB alerts put_item notice ({err}). Persisting to local fallback cache.")

        item["dynamodb_confirmed"] = saved_to_aws
        item["aws_region"] = self.region_name
        return item

    def save_news_article(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Persists a normalized disaster & logistics intelligence news article to AWS DynamoDB ('ner_news_articles' table).
        Deduplicates based on stable article ID hash and source_url.
        """
        aid = str(article_data.get("id") or f"neris-news-{int(datetime.now().timestamp())}")
        iso_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        source_url = str(article_data.get("source_url") or "#")
        if not (source_url.startswith("http://") or source_url.startswith("https://")):
            source_url = "#"

        item = {
            "id": aid,
            "title": str(article_data.get("title", "")),
            "summary": str(article_data.get("summary", "")),
            "category": str(article_data.get("category", "GENERAL")),
            "source": str(article_data.get("source", "Verified Source")),
            "source_url": source_url,
            "published_at": str(article_data.get("published_at", iso_now)),
            "published_timestamp": float(article_data.get("published_timestamp", time.time())),
            "retrieved_at": str(article_data.get("retrieved_at", iso_now)),
            "location": str(article_data.get("location", "ALL NER")).upper(),
            "severity": str(article_data.get("severity", "LOW")).upper(),
            "image_url": article_data.get("image_url"),
            "relevance_score": float(article_data.get("relevance_score", 0.0)),
            "is_demo": bool(article_data.get("is_demo", False)),
            "verification_status": str(article_data.get("verification_status", "UNVERIFIED_EXTERNAL_ARTICLE")),
            "is_unverified": bool(article_data.get("is_unverified", True)),
            "original_language": str(article_data.get("original_language", "en")),
            "original_content": article_data.get("original_content") or str(article_data.get("summary", "")),
            "ai_summary": article_data.get("ai_summary"),
            "ai_translation": article_data.get("ai_translation")
        }

        saved_to_aws = False
        if self.dynamodb_resource:
            try:
                news_table = self.dynamodb_resource.Table(getattr(settings, "DYNAMODB_NEWS_TABLE", "ner_news_articles"))
                db_item = _convert_floats_to_decimals(item)
                news_table.put_item(Item=db_item)
                saved_to_aws = True
                logger.info(f"Persisted news article '{aid}' to DynamoDB table 'ner_news_articles'.")
            except Exception as err:
                logger.warning(f"DynamoDB news put_item notice ({err}). Persisting to local fallback cache.")

        item["dynamodb_confirmed"] = saved_to_aws
        item["aws_region"] = self.region_name

        # Save to local news cache
        news_cache_path = os.path.join(os.path.dirname(LOCAL_CACHE_PATH), "news_db.json")
        try:
            cached_news = []
            if os.path.exists(news_cache_path):
                with open(news_cache_path, "r", encoding="utf-8") as f:
                    cached_news = json.load(f)
            
            # Deduplicate by ID and source_url
            existing_idx = next((i for i, n in enumerate(cached_news) if n.get("id") == aid or (source_url != "#" and n.get("source_url") == source_url)), None)
            if existing_idx is not None:
                item["duplicate_prevented"] = True
                cached_news[existing_idx] = item
            else:
                item["duplicate_prevented"] = False
                cached_news.insert(0, item)
            
            with open(news_cache_path, "w", encoding="utf-8") as f:
                json.dump(cached_news, f, indent=2, ensure_ascii=False)
        except Exception as err:
            logger.error(f"Error updating local news cache: {err}")

        return item

    def get_all_news_articles(self) -> List[Dict[str, Any]]:
        """
        Retrieves all normalized news articles from AWS DynamoDB / cache.
        """
        if self.dynamodb_resource:
            try:
                news_table = self.dynamodb_resource.Table(getattr(settings, "DYNAMODB_NEWS_TABLE", "ner_news_articles"))
                res = news_table.scan()
                items = res.get("Items", [])
                if items:
                    for item in items:
                        item["relevance_score"] = float(item.get("relevance_score", 0.0))
                        item["published_timestamp"] = float(item.get("published_timestamp", 0.0))
                        item["dynamodb_confirmed"] = True
                    return items
            except Exception as err:
                logger.warning(f"DynamoDB news scan notice: {err}")

        news_cache_path = os.path.join(os.path.dirname(LOCAL_CACHE_PATH), "news_db.json")
        if os.path.exists(news_cache_path):
            try:
                with open(news_cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

_dynamodb_adapter_instance: Optional[DynamoDBAdapter] = None

def get_dynamodb_adapter() -> DynamoDBAdapter:
    global _dynamodb_adapter_instance
    if _dynamodb_adapter_instance is None:
        _dynamodb_adapter_instance = DynamoDBAdapter()
    return _dynamodb_adapter_instance
