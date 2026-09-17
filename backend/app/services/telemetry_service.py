import math
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.models.telemetry import (
    VehicleTelemetry, TelemetryIngestResponse, ActiveFleetVehicleResponse, SimulatedVehicleState, FleetVehicleItem
)
from app.services.telemetry_simulation import get_telemetry_simulator
from app.adapters.aws_dynamodb import get_dynamodb_adapter

logger = logging.getLogger("neris.telemetry_service")

def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculates Haversine distance in km between two GPS coordinates."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

class TelemetryService:
    def __init__(self):
        self.simulator = get_telemetry_simulator()
        self.dynamodb = get_dynamodb_adapter()

    def get_simulated_telemetry(self, state: Optional[str] = None) -> List[SimulatedVehicleState]:
        """
        Returns backend simulation state for active fleet vehicles.
        """
        vehicles = self.simulator.get_vehicles(state_filter=state)
        
        # Merge with any overrides from DynamoDB
        saved_fleets = self.dynamodb.get_all_fleet_telemetry()
        saved_dict = {f["id"]: f for f in saved_fleets if "id" in f or "vehicleId" in f}
        
        res = []
        for v in vehicles:
            vid = v["vehicle_id"]
            if vid in saved_dict:
                sd = saved_dict[vid]
                v["latitude"] = float(sd.get("latitude", v["latitude"]))
                v["longitude"] = float(sd.get("longitude", v["longitude"]))
                v["speed"] = float(sd.get("speed", v["speed"]))
                v["status"] = str(sd.get("status", v["status"]))
                v["last_updated"] = str(sd.get("updatedAt", v["last_updated"]))
            res.append(SimulatedVehicleState(**v))
        return res

    def get_all_active_fleets(self, state: Optional[str] = None) -> List[ActiveFleetVehicleResponse]:
        """
        Returns active fleet vehicles mapped to vehicle response schema.
        """
        vehicles = self.simulator.get_vehicles(state_filter=state)
        saved_fleets = self.dynamodb.get_all_fleet_telemetry()
        saved_dict = {f.get("id") or f.get("vehicleId"): f for f in saved_fleets}

        fleets = []
        for v in vehicles:
            vid = v["vehicle_id"]
            if vid in saved_dict:
                sd = saved_dict[vid]
                v["latitude"] = float(sd.get("latitude", v["latitude"]))
                v["longitude"] = float(sd.get("longitude", v["longitude"]))
                v["speed"] = float(sd.get("speed", v["speed"]))
                v["status"] = str(sd.get("status", v["status"]))
                v["last_updated"] = str(sd.get("updatedAt", v["last_updated"]))

            location_name = v.get("current_route", {}).get("current_waypoint") or f"{v['state'].upper()} Corridor"
            eta_str = f"{round((100.0 - v.get('current_route', {}).get('progress_pct', 0)) / 20.0 + 1.2, 1)} hrs remaining"
            
            fleets.append(ActiveFleetVehicleResponse(
                id=v["vehicle_id"],
                driver=v.get("driver_name", "Fleet Officer"),
                category=v.get("category", "Relief Convoy"),
                payload=v.get("payload", "Essential Cargo"),
                state=v.get("state", "assam"),
                currentLocationName=location_name,
                lat=v["latitude"],
                lng=v["longitude"],
                speedKm=v["speed"],
                cargoTempC=v.get("cargo_temp_c", 4.0),
                eta=eta_str,
                status=v["status"],
                heading=v["heading"],
                fuelPercent=v["fuel"],
                route_at_risk=v.get("route_at_risk", False),
                at_risk_hazard_info=v.get("at_risk_hazard_info")
            ))
        return fleets

    def get_vehicle_by_id(self, vehicle_id: str) -> Optional[FleetVehicleItem]:
        """
        Retrieves single vehicle state by ID.
        """
        # Try DynamoDB
        stored = self.dynamodb.get_fleet_telemetry_by_id(vehicle_id)
        if stored:
            return FleetVehicleItem(**stored)

        # Fallback to simulator
        vehicles = self.simulator.get_vehicles()
        for v in vehicles:
            if v["vehicle_id"] == vehicle_id:
                return FleetVehicleItem(
                    vehicleId=v["vehicle_id"],
                    vehicle_id=v["vehicle_id"],
                    registration=v["vehicle_id"],
                    vehicleType=v.get("vehicle_type", "HEAVY_TRUCK"),
                    status=v.get("status", "CLEAR"),
                    latitude=v["latitude"],
                    longitude=v["longitude"],
                    lat=v["latitude"],
                    lng=v["longitude"],
                    speed=v["speed"],
                    heading=v["heading"],
                    cargo=v.get("payload", "Medical Supplies"),
                    updatedAt=v.get("last_updated", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
                )
        return None

    def ingest_telemetry(self, ping: VehicleTelemetry) -> TelemetryIngestResponse:
        """
        Ingests telemetry ping from vehicle transponder or simulator:
        1. Persists telemetry item to AWS DynamoDB ('ner_fleet_telemetry').
        2. Retrieves active incidents from DynamoDB.
        3. Performs Haversine distance proximity calculation between vehicle GPS and active hazards.
        4. Generates proximity alert record if within threshold (30 km).
        5. Updates vehicle status to 'ROUTE AT RISK' or 'CAUTION'.
        """
        vid = ping.vehicle_id or ping.vehicleId or "NER-MED-8041"
        v_lat = ping.current_lat if ping.current_lat is not None else ping.latitude if ping.latitude is not None else 26.1445
        v_lng = ping.current_lng if ping.current_lng is not None else ping.longitude if ping.longitude is not None else 91.7362
        v_speed = ping.speed_kmh if ping.speed_kmh is not None else ping.speed if ping.speed is not None else 40.0
        v_heading = ping.heading_degrees if ping.heading_degrees is not None else ping.heading if ping.heading is not None else 0.0

        iso_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # 1. Proximity Calculation against static hazard hotspots and active incidents
        min_dist_km = float('inf')
        nearest_incident = None

        try:
            from app.services.telemetry_simulation import HAZARD_HOTSPOTS
            for h in HAZARD_HOTSPOTS:
                dist = haversine_km(v_lat, v_lng, float(h["lat"]), float(h["lng"]))
                if dist < min_dist_km:
                    min_dist_km = dist
                    nearest_incident = {
                        "id": h["id"],
                        "title": h["name"],
                        "severity": h.get("severity", "CRITICAL"),
                        "district": h.get("state", "ASSAM").upper()
                    }
        except Exception:
            pass
        
        try:
            from app.services.incidents_service import get_incidents_service
            inc_service = get_incidents_service()
            live_incidents = inc_service.get_live_incidents()
            if live_incidents:
                for inc in live_incidents:
                    i_lat = inc.get("latitude", inc.get("lat"))
                    i_lng = inc.get("longitude", inc.get("lng"))
                    if i_lat is not None and i_lng is not None:
                        try:
                            dist = haversine_km(v_lat, v_lng, float(i_lat), float(i_lng))
                            if dist < min_dist_km:
                                min_dist_km = dist
                                nearest_incident = inc
                        except Exception:
                            pass
        except Exception as err:
            logger.warning(f"Could not load live incidents for telemetry proximity check: {err}")

        proximity_threshold_km = 25.0
        in_proximity = (nearest_incident is not None) and (min_dist_km <= proximity_threshold_km)
        
        warning_msg = None
        reroute_advised = False
        alert_created = None
        status_val = "CLEAR"

        if in_proximity and nearest_incident:
            inc_title = nearest_incident.get("title", "Active Hazard")
            inc_sev = nearest_incident.get("severity", "HIGH").upper()
            inc_id = nearest_incident.get("id", "INC-PROX")
            inc_dist_str = f"{round(min_dist_km, 1)}"
            
            warning_msg = f"WARNING: Vehicle {vid} is {inc_dist_str} km from active {inc_sev} hazard '{inc_title}'."
            reroute_advised = True
            status_val = "ROUTE AT RISK" if inc_sev == "CRITICAL" else "CAUTION"
            logger.warning(warning_msg)

            # Create Alert Record in Command Center AlertService
            try:
                from app.services.alert_service import get_alert_service
                from app.models.alert import IncidentEvaluationRequest
                alert_svc = get_alert_service()
                
                eval_req = IncidentEvaluationRequest(
                    incident_id=f"ALT-PROX-{vid}-{inc_id}",
                    title=f"PROXIMITY ALERT: Vehicle {vid} is {inc_dist_str} km from hazard",
                    severity=inc_sev,
                    district=nearest_incident.get("district", "ASSAM"),
                    description=f"Vehicle {vid} at GPS ({round(v_lat, 4)}, {round(v_lng, 4)}) is {inc_dist_str} km from active hazard '{inc_title}'. Direct reroute advised.",
                    estimated_blockage_pct=85.0 if inc_sev == "CRITICAL" else 45.0,
                    reporter=f"Automated GPS Proximity Engine ({vid})"
                )
                alert_obj = alert_svc.evaluate_incident_and_create_alert(eval_req)
                if alert_obj:
                    alert_created = alert_obj.dict()
                    alert_created["calculated_distance_km"] = round(min_dist_km, 1)
            except Exception as ex:
                logger.warning(f"Could not create proximity alert record: {ex}")

        # 2. Persist telemetry to DynamoDB
        fleet_dict = {
            "id": vid,
            "vehicleId": vid,
            "vehicle_id": vid,
            "registration": str(ping.registration or vid),
            "vehicleType": str(ping.vehicleType or "HEAVY_TRUCK"),
            "status": status_val,
            "latitude": v_lat,
            "longitude": v_lng,
            "lat": v_lat,
            "lng": v_lng,
            "speed": v_speed,
            "heading": v_heading,
            "cargo": str(ping.cargo or "Medical Supplies"),
            "cargo_type": str(ping.cargo_type or "MEDICINE"),
            "updatedAt": iso_now,
            "driver_name": str(ping.driver_name or "Ramesh Kalita"),
            "driver_phone": str(ping.driver_phone or "+91 98640 11234"),
            "route_at_risk": in_proximity,
            "at_risk_hazard_info": warning_msg
        }

        stored_res = self.dynamodb.save_fleet_telemetry(fleet_dict)

        fleet_item = FleetVehicleItem(
            vehicleId=vid,
            vehicle_id=vid,
            registration=str(ping.registration or vid),
            vehicleType=str(ping.vehicleType or "HEAVY_TRUCK"),
            status=status_val,
            latitude=v_lat,
            longitude=v_lng,
            lat=v_lat,
            lng=v_lng,
            speed=v_speed,
            heading=v_heading,
            cargo=str(ping.cargo or "Medical Supplies"),
            updatedAt=iso_now,
            driver_name=str(ping.driver_name or "Ramesh Kalita"),
            driver_phone=str(ping.driver_phone or "+91 98640 11234"),
            route_at_risk=in_proximity,
            at_risk_hazard_info=warning_msg,
            proximity_alert=alert_created
        )

        return TelemetryIngestResponse(
            status="SUCCESS",
            dynamodb_confirmed=bool(stored_res.get("dynamodb_confirmed", True)),
            vehicle=fleet_item,
            hazard_in_proximity=in_proximity,
            proximity_distance_km=round(min_dist_km, 1) if in_proximity else None,
            warning_message=warning_msg,
            reroute_advised=reroute_advised,
            alert_created=alert_created
        )

_telemetry_service_instance = None

def get_telemetry_service() -> TelemetryService:
    global _telemetry_service_instance
    if _telemetry_service_instance is None:
        _telemetry_service_instance = TelemetryService()
    return _telemetry_service_instance
