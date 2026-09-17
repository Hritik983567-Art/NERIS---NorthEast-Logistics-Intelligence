import networkx as nx
from typing import Dict, Any, List

def build_ner_transportation_graph() -> nx.Graph:
    """
    Constructs a fully interconnected NetworkX graph of 15 key NER transportation hubs
    and supply checkpoints across Assam, Meghalaya, Tripura, Mizoram, Manipur, Nagaland,
    Arunachal Pradesh, and Sikkim.
    """
    G = nx.Graph()

    # Strategic Nodes (Hubs)
    nodes_data = {
        "Guwahati": {"lat": 26.1433, "lng": 91.7898, "elevation_m": 55, "state": "Assam", "type": "PRIMARY_DEPOT", "district": "Kamrup Metropolitan"},
        "Shillong": {"lat": 25.5788, "lng": 91.8933, "elevation_m": 1525, "state": "Meghalaya", "type": "STATE_CAPITAL", "district": "East Khasi Hills"},
        "Cherrapunji": {"lat": 25.2702, "lng": 91.7323, "elevation_m": 1430, "state": "Meghalaya", "type": "HIGH_RAINFALL_ZONE", "district": "East Khasi Hills"},
        "Jowai": {"lat": 25.4452, "lng": 92.2034, "elevation_m": 1380, "state": "Meghalaya", "type": "TRANSIT_HUB", "district": "West Jaintia Hills"},
        "Silchar": {"lat": 24.8333, "lng": 92.7789, "elevation_m": 35, "state": "Assam", "type": "BARAK_VALLEY_HUB", "district": "Cachar"},
        "Agartala": {"lat": 23.8315, "lng": 91.2868, "elevation_m": 12, "state": "Tripura", "type": "STATE_CAPITAL", "district": "West Tripura"},
        "Dharmanagar": {"lat": 24.3739, "lng": 92.1644, "elevation_m": 28, "state": "Tripura", "type": "BORDER_RAILHEAD", "district": "North Tripura"},
        "Aizawl": {"lat": 23.7271, "lng": 92.7176, "elevation_m": 1132, "state": "Mizoram", "type": "STATE_CAPITAL", "district": "Aizawl"},
        "Kolasib": {"lat": 24.2241, "lng": 92.6763, "elevation_m": 620, "state": "Mizoram", "type": "GATEWAY_HUB", "district": "Kolasib"},
        "Dimapur": {"lat": 25.9068, "lng": 93.7273, "elevation_m": 145, "state": "Nagaland", "type": "RAILHEAD_DEPOT", "district": "Dimapur"},
        "Kohima": {"lat": 25.6751, "lng": 94.1086, "elevation_m": 1444, "state": "Nagaland", "type": "STATE_CAPITAL", "district": "Kohima"},
        "Imphal": {"lat": 24.8170, "lng": 93.9368, "elevation_m": 786, "state": "Manipur", "type": "STATE_CAPITAL", "district": "Imphal East"},
        "Jiribam": {"lat": 24.8016, "lng": 93.1189, "elevation_m": 42, "state": "Manipur", "type": "GATEWAY_CHECKPOINT", "district": "Jiribam"},
        "Itanagar": {"lat": 27.0844, "lng": 93.6053, "elevation_m": 320, "state": "Arunachal Pradesh", "type": "STATE_CAPITAL", "district": "Papum Pare"},
        "Tezpur": {"lat": 26.6338, "lng": 92.8006, "elevation_m": 48, "state": "Assam", "type": "BRAHMAPUTRA_BRIDGE_HUB", "district": "Sonitpur"},
        "Kaziranga": {"lat": 26.5775, "lng": 93.1711, "elevation_m": 67, "state": "Assam", "type": "NATIONAL_PARK_HIGHWAY_CORRIDOR", "district": "Golaghat"}
    }

    for node_id, data in nodes_data.items():
        G.add_node(node_id, **data)

    # Strategic Highway Edges
    edges_data = [
        ("Guwahati", "Shillong", {"length_km": 100.0, "highway_name": "NH-40", "elevation_profile": "STEEP_GHAT", "vulnerability_index": 0.45, "max_weight_tons": 35.0, "base_speed_kmh": 40.0}),
        ("Shillong", "Cherrapunji", {"length_km": 54.0, "highway_name": "SH-05", "elevation_profile": "EXTREME_SLOPE", "vulnerability_index": 0.75, "max_weight_tons": 20.0, "base_speed_kmh": 30.0}),
        ("Shillong", "Jowai", {"length_km": 66.0, "highway_name": "NH-06", "elevation_profile": "MODERATE_HILL", "vulnerability_index": 0.50, "max_weight_tons": 30.0, "base_speed_kmh": 45.0}),
        ("Jowai", "Silchar", {"length_km": 140.0, "highway_name": "NH-06", "elevation_profile": "EXTREME_SLOPE", "vulnerability_index": 0.88, "max_weight_tons": 25.0, "base_speed_kmh": 32.0}),
        ("Silchar", "Dharmanagar", {"length_km": 115.0, "highway_name": "NH-08", "elevation_profile": "MODERATE_HILL", "vulnerability_index": 0.40, "max_weight_tons": 30.0, "base_speed_kmh": 48.0}),
        ("Dharmanagar", "Agartala", {"length_km": 170.0, "highway_name": "NH-08", "elevation_profile": "PLAINS", "vulnerability_index": 0.25, "max_weight_tons": 40.0, "base_speed_kmh": 55.0}),
        ("Silchar", "Kolasib", {"length_km": 95.0, "highway_name": "NH-306", "elevation_profile": "MODERATE_HILL", "vulnerability_index": 0.60, "max_weight_tons": 22.0, "base_speed_kmh": 35.0}),
        ("Kolasib", "Aizawl", {"length_km": 83.0, "highway_name": "NH-54", "elevation_profile": "STEEP_GHAT", "vulnerability_index": 0.70, "max_weight_tons": 20.0, "base_speed_kmh": 30.0}),
        ("Guwahati", "Tezpur", {"length_km": 175.0, "highway_name": "NH-27", "elevation_profile": "PLAINS", "vulnerability_index": 0.20, "max_weight_tons": 45.0, "base_speed_kmh": 65.0}),
        ("Tezpur", "Itanagar", {"length_km": 155.0, "highway_name": "NH-15", "elevation_profile": "MODERATE_HILL", "vulnerability_index": 0.55, "max_weight_tons": 30.0, "base_speed_kmh": 45.0}),
        ("Guwahati", "Dimapur", {"length_km": 280.0, "highway_name": "NH-27", "elevation_profile": "PLAINS", "vulnerability_index": 0.30, "max_weight_tons": 45.0, "base_speed_kmh": 60.0}),
        ("Dimapur", "Kohima", {"length_km": 74.0, "highway_name": "NH-29", "elevation_profile": "STEEP_GHAT", "vulnerability_index": 0.82, "max_weight_tons": 25.0, "base_speed_kmh": 35.0}),
        ("Kohima", "Imphal", {"length_km": 138.0, "highway_name": "NH-02", "elevation_profile": "EXTREME_SLOPE", "vulnerability_index": 0.85, "max_weight_tons": 24.0, "base_speed_kmh": 32.0}),
        ("Silchar", "Jiribam", {"length_km": 50.0, "highway_name": "NH-37", "elevation_profile": "MODERATE_HILL", "vulnerability_index": 0.50, "max_weight_tons": 28.0, "base_speed_kmh": 40.0}),
        ("Jiribam", "Imphal", {"length_km": 222.0, "highway_name": "NH-37", "elevation_profile": "EXTREME_SLOPE", "vulnerability_index": 0.78, "max_weight_tons": 22.0, "base_speed_kmh": 30.0}),
        ("Tezpur", "Kaziranga", {"length_km": 65.0, "highway_name": "NH-715", "elevation_profile": "PLAINS", "vulnerability_index": 0.35, "max_weight_tons": 40.0, "base_speed_kmh": 55.0}),
        ("Guwahati", "Kaziranga", {"length_km": 195.0, "highway_name": "NH-27", "elevation_profile": "PLAINS", "vulnerability_index": 0.25, "max_weight_tons": 45.0, "base_speed_kmh": 60.0}),
        ("Kaziranga", "Dimapur", {"length_km": 140.0, "highway_name": "NH-29", "elevation_profile": "PLAINS", "vulnerability_index": 0.30, "max_weight_tons": 40.0, "base_speed_kmh": 50.0})
    ]

    for u, v, attrs in edges_data:
        G.add_edge(u, v, **attrs)

    return G
