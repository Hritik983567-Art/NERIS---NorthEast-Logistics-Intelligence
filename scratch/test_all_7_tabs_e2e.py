import sys
import os
import json
import time

# Add backend directory to path
sys.path.insert(0, os.path.abspath("backend"))

from fastapi.testclient import TestClient
from app.main import app
from app.adapters.aws_cognito import create_jwt_token

client = TestClient(app)

# Create mock JWT tokens
admin_token = create_jwt_token("admin_user", "COMMANDER")
field_token = create_jwt_token("field_user", "FIELD_OFFICER")
headers = {"Authorization": f"Bearer {admin_token}"}

results = {}

import traceback

def run_test(tab_name, test_func):
    try:
        res = test_func()
        results[tab_name] = {"passed": True, "details": res}
        print(f"[PASS] TAB [{tab_name}]: {res}")
    except Exception as e:
        tb = traceback.format_exc()
        results[tab_name] = {"passed": False, "error": f"{type(e).__name__}: {str(e)}", "traceback": tb}
        print(f"[FAIL] TAB [{tab_name}]: {type(e).__name__}: {str(e)}\n{tb}")

# TAB 1: MAP
def test_tab_map():
    r1 = client.get("/api/v1/network/nodes", headers=headers)
    assert r1.status_code == 200, f"Nodes status {r1.status_code}"
    nodes = r1.json()
    
    r2 = client.get("/api/v1/network/edges", headers=headers)
    assert r2.status_code == 200, f"Edges status {r2.status_code}"
    edges = r2.json()
    
    r3 = client.get("/api/v1/network/corridors", headers=headers)
    assert r3.status_code == 200, f"Corridors status {r3.status_code}"
    corridors = r3.json()
    
    return f"Nodes: {len(nodes)}, Edges: {len(edges)}, Dynamic Corridors: {len(corridors)}"

# TAB 2: PLANNER
def test_tab_planner():
    payload = {
        "origin": "Guwahati",
        "destination": "Silchar",
        "vehicleType": "HEAVY_CONVOY",
        "cargoType": "MEDICINE",
        "convoy_weight_tons": 18.5,
        "weather_condition": "MONSOON_STORM"
    }
    r = client.post("/api/v1/routes/compute", json=payload, headers=headers)
    assert r.status_code == 200, f"Compute route status {r.status_code} - {r.text}"
    data = r.json()
    assert "path_nodes" in data and "total_distance_km" in data
    return f"Path: {data.get('path_nodes', [])}, Distance: {data.get('total_distance_km')}km, Strategy: {data.get('decision_explanation')[:50]}..."

# TAB 3: FLEET
def test_tab_fleet():
    r1 = client.get("/api/v1/fleet", headers=headers)
    assert r1.status_code == 200, f"Fleet status {r1.status_code}"
    fleet_data = r1.json()
    
    ping_payload = {
        "vehicle_id": "TRK-01",
        "latitude": 26.1433,
        "longitude": 91.7898,
        "speed_kmh": 45.5,
        "fuel_level": 82.0,
        "status": "IN_TRANSIT"
    }
    r2 = client.post("/api/v1/telemetry/ping", json=ping_payload, headers=headers)
    assert r2.status_code == 200, f"Ping status {r2.status_code}"
    return f"Fleet size: {len(fleet_data)}, Telemetry ping processed successfully"

# TAB 4: INCIDENTS
def test_tab_incidents():
    r1 = client.get("/api/v1/incidents", headers=headers)
    assert r1.status_code == 200, f"Get incidents status {r1.status_code}"
    incidents = r1.json()
    inc_count = len(incidents) if isinstance(incidents, list) else len(incidents.get('incidents', []))
    
    inc_payload = {
        "title": "Landslide on NH-6 Highway",
        "type": "LANDSLIDE",
        "severity": "CRITICAL",
        "latitude": 25.5788,
        "longitude": 91.8933,
        "description": "Major rockfall blocking both lanes near Jowai.",
        "affected_radius_km": 5.0
    }
    r2 = client.post("/api/v1/incidents", json=inc_payload, headers=headers)
    assert r2.status_code == 201, f"Create incident status {r2.status_code} - {r2.text}"
    inc_res = r2.json()
    assert "incident" in inc_res and "id" in inc_res["incident"]
    return f"Incidents retrieved: {inc_count}, Created Incident ID: {inc_res['incident']['id']}"

# TAB 5: ANALYTICS
def test_tab_analytics():
    r1 = client.get("/api/v1/network/overview", headers=headers)
    assert r1.status_code == 200, f"Network overview status {r1.status_code}"
    overview = r1.json()
    
    r2 = client.get("/api/v1/incidents", headers=headers)
    assert r2.status_code == 200, f"Incidents status {r2.status_code}"
    inc_data = r2.json()
    inc_list = inc_data.get("incidents", []) if isinstance(inc_data, dict) else inc_data
    return f"Connectivity Index: {overview.get('connectivity_index')}%, Total Hubs: {overview.get('total_hubs')}, Active Incidents: {len(inc_list)}"

# TAB 6: ALERTS
def test_tab_alerts():
    r1 = client.get("/api/v1/alerts", headers=headers)
    assert r1.status_code == 200, f"Get alerts status {r1.status_code}"
    alerts_data = r1.json()
    
    sos_payload = {
        "vehicle_id": "TRK-01",
        "reason": "Flash flood trapping convoy at East Khasi Hills junction",
        "latitude": 25.5788,
        "longitude": 91.8933,
        "urgency_level": "EMERGENCY_SOS"
    }
    r2 = client.post("/api/v1/alerts/sos-dispatch", json=sos_payload, headers=headers)
    assert r2.status_code == 201, f"SOS dispatch status {r2.status_code} - {r2.text}"
    sos_res = r2.json()
    return f"Alerts retrieved: {len(alerts_data)}, SOS Alert Dispatched ID: {sos_res.get('alert_id')}"

# TAB 7: NEWS
def test_tab_news():
    r1 = client.get("/api/news?category=ALL", headers=headers)
    assert r1.status_code == 200, f"Get news status {r1.status_code}"
    news_articles = r1.json()
    
    return f"News items fetched: {len(news_articles)}"

# TAB 8: CRITICAL NEGATIVE SECURITY SUITE (FINDINGS 1, 2, 3)
def test_negative_security_suite():
    # --- FINDING 1: AUTHENTICATION BYPASS REJECTION ---
    # 1.1 Login attempt with unregistered username must fail with HTTP 401
    fake_login = client.post("/api/v1/auth/login", json={"username": "unregistered_hacker_99", "password": "anypassword"})
    assert fake_login.status_code == 401, f"Unregistered user login should return 401, got {fake_login.status_code}"

    # 1.2 Login attempt with registered username but wrong password must fail with HTTP 401
    bad_pass_login = client.post("/api/v1/auth/login", json={"username": "commander", "password": "WrongPassword123!"})
    assert bad_pass_login.status_code == 401, f"Wrong password login should return 401, got {bad_pass_login.status_code}"

    # --- FINDING 2: UNAUTHENTICATED FLEET CONTROL & SURVEILLANCE REJECTION ---
    # 2.1 Unauthenticated telemetry ping must fail with HTTP 401
    unauth_ping = client.post("/api/v1/telemetry/ping", json={"vehicle_id": "SPOOF-01", "latitude": 26.0, "longitude": 91.0, "speed_kmh": 50})
    assert unauth_ping.status_code == 401, f"Unauthenticated telemetry ping should return 401, got {unauth_ping.status_code}"

    # 2.2 Unauthenticated active fleet query must fail with HTTP 401
    unauth_fleet = client.get("/api/v1/fleet")
    assert unauth_fleet.status_code == 401, f"Unauthenticated fleet query should return 401, got {unauth_fleet.status_code}"

    # 2.3 Unauthenticated single vehicle lookup must fail with HTTP 401
    unauth_single = client.get("/api/v1/fleet/TRK-01")
    assert unauth_single.status_code == 401, f"Unauthenticated single vehicle query should return 401, got {unauth_single.status_code}"

    # --- FINDING 3: BOLA & BATCH IDENTITY OVERRIDE REJECTION ---
    # 3.1 Create incident with Officer A
    inc_payload = {
        "title": "BOLA Security Blockade Test",
        "description": "Testing ownership boundary",
        "type": "LANDSLIDE",
        "severity": "HIGH",
        "latitude": 25.9,
        "longitude": 91.8
    }
    officer_a_token = create_jwt_token("officer_a", "FIELD_OFFICER")
    c1 = client.post("/api/v1/incidents", json=inc_payload, headers={"Authorization": f"Bearer {officer_a_token}"})
    assert c1.status_code == 201, f"Officer A incident create failed: {c1.text}"
    inc_id = c1.json()["incident"]["id"]

    # 3.2 Officer B attempts to modify Officer A's incident -> BOLA check must reject with HTTP 403
    officer_b_token = create_jwt_token("officer_b", "FIELD_OFFICER")
    u1 = client.patch(f"/api/v1/incidents/{inc_id}", json={"description": "Hacked edit attempt"}, headers={"Authorization": f"Bearer {officer_b_token}"})
    assert u1.status_code == 403, f"BOLA edit violation should return 403, got {u1.status_code}"

    # 3.3 Batch sync attempt with client-forged reporter identity -> Server MUST override reporter with session identity
    batch_item = {
        "operation_id": f"OP-BATCH-TEST-{int(time.time())}",
        "title": "Batch Identity Hardening Test",
        "description": "Testing client reporter override",
        "type": "FLASH_FLOOD",
        "severity": "CRITICAL",
        "latitude": 26.1,
        "longitude": 91.7,
        "reporter": "FORGED_SUPER_ADMIN_NAME"
    }
    batch_res = client.post("/api/v1/incidents/batch-sync", json={"items": [batch_item]}, headers={"Authorization": f"Bearer {officer_a_token}"})
    assert batch_res.status_code == 200, f"Batch sync failed: {batch_res.text}"
    synced_inc = batch_res.json()["results"][0]["incident"]
    assert synced_inc.get("reported_by") == "officer_a", f"Batch sync reporter identity spoofed! Got {synced_inc.get('reported_by')}, expected 'officer_a'"

    return "All 3 Critical Negative Security Findings successfully remediated and verified (401, 403, & session identity overrides enforced)."

print("=== STARTING ALL 7 TABS + SECURITY E2E AUDIT ===")
run_test("map", test_tab_map)
run_test("planner", test_tab_planner)
run_test("fleet", test_tab_fleet)
run_test("incidents", test_tab_incidents)
run_test("analytics", test_tab_analytics)
run_test("alerts", test_tab_alerts)
run_test("news", test_tab_news)
run_test("negative_security_suite", test_negative_security_suite)

print("\n=== FINAL AUDIT RESULT ===")
passed_count = sum(1 for v in results.values() if v.get("passed"))
print(f"TOTAL PASSED: {passed_count} / {len(results)}")
print(json.dumps(results, indent=2))

if passed_count < len(results):
    sys.exit(1)


