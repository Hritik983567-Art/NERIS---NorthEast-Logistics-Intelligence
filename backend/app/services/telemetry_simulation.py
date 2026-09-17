import math
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger("neris.telemetry_simulation")

# Predefined highway route vectors across Northeast India with strategic waypoints
PREDEFINED_ROUTES: Dict[str, Dict[str, Any]] = {
    "ROUTE-NH40-MEG": {
        "route_id": "ROUTE-NH40-MEG",
        "name": "Guwahati - Shillong - Dawki Corridor (NH-40 / NH-06)",
        "origin": "Guwahati Central FCI Depot (Assam)",
        "destination": "Dawki Border Post (Meghalaya)",
        "total_distance_km": 175.0,
        "waypoints": [
            {"name": "Guwahati Depot", "lat": 26.1445, "lng": 91.7362},
            {"name": "Nongpoh Checkpoint", "lat": 25.9231, "lng": 91.8710},
            {"name": "Shillong Bypass", "lat": 25.5788, "lng": 91.8933},
            {"name": "Jowai Ridge Pass", "lat": 25.4452, "lng": 92.2034},
            {"name": "Dawki Border Post", "lat": 25.1856, "lng": 92.0125}
        ]
    },
    "ROUTE-NH37-MAN": {
        "route_id": "ROUTE-NH37-MAN",
        "name": "Guwahati - Dimapur - Kohima - Imphal Lifeline (NH-27 / NH-2)",
        "origin": "Guwahati Logistics Yard (Assam)",
        "destination": "Imphal Central Depot (Manipur)",
        "total_distance_km": 485.0,
        "waypoints": [
            {"name": "Guwahati Central", "lat": 26.1445, "lng": 91.7362},
            {"name": "Nagaon Junction", "lat": 26.3456, "lng": 92.6841},
            {"name": "Dimapur Railhead", "lat": 25.9063, "lng": 93.7271},
            {"name": "Kohima Ridge Pass", "lat": 25.6747, "lng": 94.1077},
            {"name": "Senapati Corridor", "lat": 25.2688, "lng": 94.0150},
            {"name": "Imphal Valley Yard", "lat": 24.8170, "lng": 93.9368}
        ]
    },
    "ROUTE-NH54-MIZ": {
        "route_id": "ROUTE-NH54-MIZ",
        "name": "Silchar - Kolasib - Aizawl Arterial Corridor (NH-54)",
        "origin": "Silchar Goods Yard (Assam)",
        "destination": "Aizawl Distribution Hub (Mizoram)",
        "total_distance_km": 180.0,
        "waypoints": [
            {"name": "Silchar Rail Yard", "lat": 24.8333, "lng": 92.7789},
            {"name": "Kolasib Transit Hub", "lat": 24.2255, "lng": 92.6788},
            {"name": "Aizawl North Gate", "lat": 23.7271, "lng": 92.7176}
        ]
    },
    "ROUTE-NH10-SIK": {
        "route_id": "ROUTE-NH10-SIK",
        "name": "Siliguri - Rangpo - Gangtok Teesta Highway (NH-10)",
        "origin": "Siliguri Junction (West Bengal)",
        "destination": "Gangtok State Yard (Sikkim)",
        "total_distance_km": 114.0,
        "waypoints": [
            {"name": "Siliguri Logistics Hub", "lat": 26.7271, "lng": 88.3953},
            {"name": "Sevoke Bridge Pass", "lat": 26.8912, "lng": 88.4715},
            {"name": "Rangpo Border Checkpost", "lat": 27.1764, "lng": 88.5321},
            {"name": "Gangtok Central Depot", "lat": 27.3389, "lng": 88.6065}
        ]
    },
    "ROUTE-NH13-ARU": {
        "route_id": "ROUTE-NH13-ARU",
        "name": "Bhalukpong - Sela Tunnel - Tawang High Corridor (NH-13)",
        "origin": "Bhalukpong Gate (Arunachal Pradesh)",
        "destination": "Tawang Forward Base (Arunachal Pradesh)",
        "total_distance_km": 290.0,
        "waypoints": [
            {"name": "Bhalukpong Entry Gate", "lat": 27.0124, "lng": 92.6412},
            {"name": "Bomdila Pass", "lat": 27.2641, "lng": 92.4185},
            {"name": "Sela Tunnel Approach", "lat": 27.5082, "lng": 92.1034},
            {"name": "Tawang Strategic Hub", "lat": 27.5861, "lng": 91.8594}
        ]
    },
    "ROUTE-NH08-TRI": {
        "route_id": "ROUTE-NH08-TRI",
        "name": "Dharmanagar - Kailashahar - Agartala Logistics Line (NH-08)",
        "origin": "Dharmanagar Yard (Tripura)",
        "destination": "Agartala Central Yard (Tripura)",
        "total_distance_km": 170.0,
        "waypoints": [
            {"name": "Dharmanagar Railhead", "lat": 24.3821, "lng": 92.1645},
            {"name": "Kailashahar Depot", "lat": 24.3210, "lng": 92.0112},
            {"name": "Agartala Central Hub", "lat": 23.8315, "lng": 91.2868}
        ]
    }
}

# Initial Fleet Convoys Configuration
INITIAL_CONVOYS = [
    {
        "vehicle_id": "NER-MED-8041",
        "driver_name": "Tashi Norbu",
        "driver_phone": "+91 94361 11234",
        "category": "Medicines & Essential Drugs",
        "payload": "Life-Saving Vaccines & Insulin (Cold-Chain)",
        "cargo_type": "MEDICINE",
        "state": "arunachal pradesh",
        "origin": "Guwahati Central Depot",
        "destination": "Tawang District Hospital",
        "route_id": "ROUTE-NH40-MEG",
        "speed": 38.0,
        "fuel": 84.5,
        "cargo_temp_c": 3.2,
        "vehicle_type": "Refrigerated Truck 10T"
    },
    {
        "vehicle_id": "NER-FOOD-9102",
        "driver_name": "Bikramjit Singh",
        "driver_phone": "+91 98620 55432",
        "category": "Food Grains (FCI Supply)",
        "payload": "18 Tonnes Fortified Rice & Pulses",
        "cargo_type": "GRAIN",
        "state": "manipur",
        "origin": "Silchar FCI Hub",
        "destination": "Imphal West Distribution Center",
        "route_id": "ROUTE-NH37-MAN",
        "speed": 32.0,
        "fuel": 62.0,
        "cargo_temp_c": 24.5,
        "vehicle_type": "Multi-Axle Heavy Hauler"
    },
    {
        "vehicle_id": "NER-OXY-3055",
        "driver_name": "Debashish Das",
        "driver_phone": "+91 97740 88219",
        "category": "Liquid Medical Oxygen",
        "payload": "12,000 Liters Cryogenic Oxygen Tanker",
        "cargo_type": "MEDICINE",
        "state": "meghalaya",
        "origin": "Bongaigaon Refinery",
        "destination": "NEIGRIHMS Shillong",
        "route_id": "ROUTE-NH40-MEG",
        "speed": 52.0,
        "fuel": 88.0,
        "cargo_temp_c": -182.0,
        "vehicle_type": "Cryogenic Oxygen Tanker"
    },
    {
        "vehicle_id": "NER-MAT-1104",
        "driver_name": "Renedy Chingtham",
        "driver_phone": "+91 94022 33104",
        "category": "Bridge Construction Materials",
        "payload": "Modular Bailey Bridge Steel Girders",
        "cargo_type": "MATERIALS",
        "state": "nagaland",
        "origin": "Dimapur Logistics Yard",
        "destination": "Tuensang BRO Detachment",
        "route_id": "ROUTE-NH37-MAN",
        "speed": 28.0,
        "fuel": 54.0,
        "cargo_temp_c": 22.0,
        "vehicle_type": "Heavy Equipment Carrier"
    },
    {
        "vehicle_id": "NER-AGRI-5590",
        "driver_name": "Lalthlamuana",
        "driver_phone": "+91 96121 99042",
        "category": "Horticulture & Organic Spices",
        "payload": "8.5 Tonnes Export Grade Bird's Eye Chilli & Pineapple",
        "cargo_type": "GRAIN",
        "state": "mizoram",
        "origin": "Aizawl Agri Market",
        "destination": "Guwahati Cargo Airport Complex",
        "route_id": "ROUTE-NH54-MIZ",
        "speed": 46.0,
        "fuel": 82.0,
        "cargo_temp_c": 18.5,
        "vehicle_type": "Insulated Cargo Van"
    },
    {
        "vehicle_id": "NER-RAW-4105",
        "driver_name": "D. Lepcha",
        "driver_phone": "+91 97330 44120",
        "category": "Teesta Flood Emergency Relief & Medical Kits",
        "payload": "15 Tonnes Disaster Aid & Water Purifiers",
        "cargo_type": "MEDICINE",
        "state": "sikkim",
        "origin": "Siliguri Goods Yard",
        "destination": "Gangtok State Depot",
        "route_id": "ROUTE-NH10-SIK",
        "speed": 38.0,
        "fuel": 91.0,
        "cargo_temp_c": 12.0,
        "vehicle_type": "Emergency Aid Convoy"
    },
    {
        "vehicle_id": "NER-MED-5012",
        "driver_name": "T. Tsering",
        "driver_phone": "+91 94020 88712",
        "category": "High-Altitude Medical Plasma & Antivenom",
        "payload": "800 Units Plasma & High-Altitude Equipment",
        "cargo_type": "MEDICINE",
        "state": "arunachal pradesh",
        "origin": "Bhalukpong Depot",
        "destination": "Tawang Forward Medical Base",
        "route_id": "ROUTE-NH13-ARU",
        "speed": 26.5,
        "fuel": 58.0,
        "cargo_temp_c": 2.2,
        "vehicle_type": "4x4 All-Terrain Ambulance Convoy"
    }
]

# Known active hazard hotspots for hazard proximity checks
HAZARD_HOTSPOTS = [
    {
        "id": "HAZ-001",
        "name": "NH-06 Jowai Ridge Landslide & Blockade",
        "lat": 25.4452,
        "lng": 92.2034,
        "severity": "CRITICAL",
        "hazard_type": "LANDSLIDE",
        "state": "meghalaya"
    },
    {
        "id": "HAZ-002",
        "name": "NH-37 Senapati Mudslide Corridor",
        "lat": 25.2688,
        "lng": 94.0150,
        "severity": "CRITICAL",
        "hazard_type": "LANDSLIDE",
        "state": "manipur"
    },
    {
        "id": "HAZ-003",
        "name": "NH-10 Rangpo Teesta Waterlogging",
        "lat": 27.1764,
        "lng": 88.5321,
        "severity": "HIGH",
        "hazard_type": "FLOOD",
        "state": "sikkim"
    }
]


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculates geodesic distance between two points in kilometers."""
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return 6371.0 * c


def calculate_heading_degrees(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculates compass heading direction angle (0 to 360 degrees) between two waypoints."""
    y = math.sin(math.radians(lng2 - lng1)) * math.cos(math.radians(lat2))
    x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(math.radians(lng2 - lng1))
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360.0) % 360.0


class TelemetrySimulator:
    """
    Deterministic backend simulation engine for NERIS Fleet Convoys.
    Advances vehicle coordinates along predefined highway routes, calculates fuel, speed, heading,
    and cross-references spatial disaster hazards for ROUTE AT RISK warnings.
    """
    def __init__(self):
        self._vehicles: Dict[str, Dict[str, Any]] = {}
        self._last_simulation_time: float = time.time()
        self._initialize_vehicles()

    def _initialize_vehicles(self):
        for config in INITIAL_CONVOYS:
            v_id = config["vehicle_id"]
            route_info = PREDEFINED_ROUTES.get(config["route_id"], PREDEFINED_ROUTES["ROUTE-NH40-MEG"])
            waypoints = route_info["waypoints"]
            
            initial_lat = waypoints[0]["lat"]
            initial_lng = waypoints[0]["lng"]
            heading = calculate_heading_degrees(initial_lat, initial_lng, waypoints[1]["lat"], waypoints[1]["lng"])

            self._vehicles[v_id] = {
                "vehicle_id": v_id,
                "driver_name": config["driver_name"],
                "driver_phone": config["driver_phone"],
                "category": config["category"],
                "payload": config["payload"],
                "cargo_type": config["cargo_type"],
                "state": config["state"],
                "origin": config["origin"],
                "destination": config["destination"],
                "base_speed": config["speed"],
                "speed": config["speed"],
                "fuel": config["fuel"],
                "base_cargo_temp_c": config["cargo_temp_c"],
                "cargo_temp_c": config["cargo_temp_c"],
                "vehicle_type": config["vehicle_type"],
                "latitude": initial_lat,
                "longitude": initial_lng,
                "heading": round(heading, 1),
                "status": "clear",
                "route_at_risk": False,
                "at_risk_hazard_info": None,
                "route_id": route_info["route_id"],
                "route_name": route_info["name"],
                "waypoint_index": 0,
                "direction": 1,  # 1 for forward, -1 for reverse
                "segment_progress": 0.0,
                "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "current_route": {
                    "route_id": route_info["route_id"],
                    "name": route_info["name"],
                    "origin": route_info["origin"],
                    "destination": route_info["destination"],
                    "total_distance_km": route_info["total_distance_km"],
                    "waypoints": waypoints,
                    "current_waypoint": waypoints[0]["name"]
                }
            }

    def step_simulation(self):
        """
        Advances all vehicles along their predefined routes based on speed & time delta,
        with realistic live telemetry oscillations for speed, compass bearing, fuel, and temperature.
        """
        now = time.time()
        delta_seconds = max(0.5, min(10.0, now - self._last_simulation_time))
        self._last_simulation_time = now
        retrieved_at_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        for v_id, v in self._vehicles.items():
            route_info = PREDEFINED_ROUTES.get(v["route_id"])
            if not route_info:
                continue
                
            waypoints = route_info["waypoints"]
            n_waypoints = len(waypoints)
            if n_waypoints < 2:
                continue

            current_idx = v["waypoint_index"]
            next_idx = current_idx + v["direction"]

            if next_idx >= n_waypoints:
                v["direction"] = -1
                next_idx = current_idx - 1
            elif next_idx < 0:
                v["direction"] = 1
                next_idx = current_idx + 1

            wp_start = waypoints[current_idx]
            wp_end = waypoints[next_idx]

            # Step along segment by speed (speed in km/h -> km per sec = speed / 3600)
            dist_seg_km = max(0.1, haversine_km(wp_start["lat"], wp_start["lng"], wp_end["lat"], wp_end["lng"]))
            
            # Smooth dynamic speed variation representing realistic terrain driving
            base_sp = v.get("base_speed", 35.0)
            hash_offset = sum(ord(c) for c in v_id)
            phase = (now + hash_offset % 100)
            speed_delta = (math.sin(phase / 2.2) * 5.5) + (math.cos(phase / 3.8) * 3.0)
            current_speed = round(max(15.0, min(75.0, base_sp + speed_delta)), 1)
            v["speed"] = current_speed

            step_km = (current_speed / 3600.0) * delta_seconds * 12.0  # Time acceleration factor for visible UI movement

            v["segment_progress"] += step_km / dist_seg_km

            if v["segment_progress"] >= 1.0:
                v["segment_progress"] = 0.0
                v["waypoint_index"] = next_idx
                current_idx = next_idx
                next_idx = current_idx + v["direction"]
                if next_idx >= n_waypoints:
                    v["direction"] = -1
                    next_idx = current_idx - 1
                elif next_idx < 0:
                    v["direction"] = 1
                    next_idx = current_idx + 1
                wp_start = waypoints[current_idx]
                wp_end = waypoints[next_idx]

            prog = v["segment_progress"]
            new_lat = wp_start["lat"] + (wp_end["lat"] - wp_start["lat"]) * prog
            new_lng = wp_start["lng"] + (wp_end["lng"] - wp_start["lng"]) * prog

            v["latitude"] = round(new_lat, 5)
            v["longitude"] = round(new_lng, 5)
            
            # Base heading with micro steering variation
            base_heading = calculate_heading_degrees(wp_start["lat"], wp_start["lng"], wp_end["lat"], wp_end["lng"])
            steering_jitter = math.sin(now * 1.5 + hash_offset % 10) * 0.8
            v["heading"] = round((base_heading + steering_jitter) % 360.0, 1)
            
            # Micro cargo temperature oscillation
            base_temp = v.get("base_cargo_temp_c", 22.0)
            temp_jitter = math.sin(now * 0.7 + hash_offset % 7) * 0.2
            v["cargo_temp_c"] = round(base_temp + temp_jitter, 1)

            v["last_updated"] = retrieved_at_str
            
            # Fuel slowly decreases and refills when below 10%
            v["fuel"] = round(max(5.0, v["fuel"] - 0.04), 1)
            if v["fuel"] <= 8.0:
                v["fuel"] = 98.0

            # Update current route snapshot
            v["current_route"]["current_waypoint"] = wp_start["name"]
            v["current_route"]["progress_pct"] = round((v["waypoint_index"] / max(1, n_waypoints - 1)) * 100.0, 1)

            # Evaluate spatial hazard proximity for ROUTE AT RISK status
            self._evaluate_route_risk(v)

    def _evaluate_route_risk(self, vehicle: Dict[str, Any]):
        """
        Cross-references active disaster hazard hotspots and DynamoDB live incidents to determine if vehicle route is at risk.
        """
        v_lat = vehicle["latitude"]
        v_lng = vehicle["longitude"]
        
        at_risk = False
        risk_info = None

        # 1. Check Static Hazard Hotspots
        for hazard in HAZARD_HOTSPOTS:
            dist = haversine_km(v_lat, v_lng, hazard["lat"], hazard["lng"])
            if dist <= 25.0:
                at_risk = True
                risk_info = f"{hazard['name']} ({round(dist, 1)} km away)"
                break

        # 2. Check Live Incidents from DynamoDB / Incidents Service
        if not at_risk:
            try:
                from app.services.incidents_service import get_incidents_service
                inc_service = get_incidents_service()
                live_incidents = inc_service.get_live_incidents()
                for inc in live_incidents:
                    sev = str(inc.get("severity", "")).upper()
                    if sev in ["CRITICAL", "HIGH"]:
                        inc_lat = inc.get("lat") or inc.get("latitude")
                        inc_lng = inc.get("lng") or inc.get("longitude")
                        if inc_lat is not None and inc_lng is not None:
                            dist = haversine_km(v_lat, v_lng, float(inc_lat), float(inc_lng))
                            if dist <= 30.0:
                                at_risk = True
                                inc_type = inc.get("hazard_type") or inc.get("type") or "HAZARD"
                                loc = inc.get("location_name") or inc.get("district") or "Corridor"
                                risk_info = f"Live Incident ({inc_type} at {loc}, {round(dist, 1)} km away)"
                                break
            except Exception as ex:
                logger.debug(f"Error checking live incidents for telemetry risk: {ex}")

        vehicle["route_at_risk"] = at_risk
        vehicle["at_risk_hazard_info"] = risk_info

        if at_risk:
            vehicle["status"] = "ROUTE AT RISK"
        elif vehicle["status"] in ["ROUTE AT RISK", "caution", "blocked"]:
            vehicle["status"] = "clear"

    def get_vehicles(self, state_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        self.step_simulation()
        vehicles_list = []
        for v in self._vehicles.values():
            if state_filter and state_filter.lower() != "all" and v["state"].lower() != state_filter.lower():
                continue
            vehicles_list.append(v)
        return vehicles_list

    def get_vehicle_by_id(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        self.step_simulation()
        return self._vehicles.get(vehicle_id)


_simulator_instance: Optional[TelemetrySimulator] = None

def get_telemetry_simulator() -> TelemetrySimulator:
    global _simulator_instance
    if _simulator_instance is None:
        _simulator_instance = TelemetrySimulator()
    return _simulator_instance
