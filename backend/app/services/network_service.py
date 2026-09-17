import logging
import networkx as nx
from typing import List, Dict, Any, Optional
from app.data.ner_nodes_edges import build_ner_transportation_graph
from app.models.network import NetworkNodeModel, NetworkEdgeModel, NetworkOverviewResponse, CorridorStatusModel
from app.adapters.aws_dynamodb import get_dynamodb_adapter

logger = logging.getLogger("ner_logitrack.network_service")

class NetworkGraphService:
    def __init__(self):
        self.graph: nx.Graph = build_ner_transportation_graph()
        self.dynamodb = get_dynamodb_adapter()
        logger.info("NetworkGraphService initialized with NetworkX graph.")

    def get_all_nodes(self, state: str = None) -> List[NetworkNodeModel]:
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            if state and data.get("state", "").lower() != state.lower():
                continue
            nodes.append(NetworkNodeModel(
                id=node_id,
                lat=data.get("lat", 0.0),
                lng=data.get("lng", 0.0),
                elevation_m=data.get("elevation_m", 0),
                state=data.get("state", "Unknown"),
                district=data.get("district"),
                type=data.get("type", "HUB")
            ))
        return nodes

    def get_all_edges(self) -> List[NetworkEdgeModel]:
        edges = []
        for u, v, data in self.graph.edges(data=True):
            edges.append(NetworkEdgeModel(
                from_node=u,
                to_node=v,
                length_km=data.get("length_km", 50.0),
                highway_name=data.get("highway_name", "NH-00"),
                elevation_profile=data.get("elevation_profile", "PLAINS"),
                vulnerability_index=data.get("vulnerability_index", 0.3),
                max_weight_tons=data.get("max_weight_tons", 30.0),
                base_speed_kmh=data.get("base_speed_kmh", 40.0)
            ))
        return edges

    def get_corridor_statuses(self, state_filter: Optional[str] = None) -> List[CorridorStatusModel]:
        incidents = self.dynamodb.get_all_incidents()
        edges = self.get_all_edges()
        corridors_map: Dict[str, CorridorStatusModel] = {}

        for e in edges:
            hname = e.highway_name
            node_from_data = self.graph.nodes.get(e.from_node, {})
            node_state = node_from_data.get("state", "ASSAM")

            if state_filter and state_filter.lower() != 'all' and node_state.lower() != state_filter.lower():
                continue

            affecting = [
                inc for inc in incidents
                if str(inc.get("status", "")).upper() != "RESOLVED" and (
                    hname.lower() in str(inc.get("title", "")).lower() or
                    hname.lower() in str(inc.get("location_name", "")).lower() or
                    e.from_node.lower() in str(inc.get("title", "")).lower() or
                    e.to_node.lower() in str(inc.get("title", "")).lower()
                )
            ]

            status_val = "clear"
            if any(str(inc.get("severity", "")).upper() == "CRITICAL" or float(inc.get("estimated_blockage_pct", 0) or 0) >= 80 for inc in affecting):
                status_val = "blocked"
            elif len(affecting) > 0 or e.vulnerability_index >= 0.7:
                status_val = "caution"

            corridors_map[hname] = CorridorStatusModel(
                id=hname,
                name=f"{e.from_node} - {e.to_node} Corridor ({hname})",
                route=f"{e.from_node} -> {e.to_node}",
                state=node_state,
                status=status_val,
                active_incidents_count=len(affecting),
                vulnerability_index=e.vulnerability_index,
                length_km=e.length_km,
                max_weight_tons=e.max_weight_tons
            )

        return list(corridors_map.values())

    def get_overview(self) -> NetworkOverviewResponse:
        nodes = self.get_all_nodes()
        edges = self.get_all_edges()
        states = sorted(list(set(n.state for n in nodes)))
        high_vul = sum(1 for e in edges if e.vulnerability_index >= 0.70)
        avg_elev = round(sum(n.elevation_m for n in nodes) / max(1, len(nodes)), 1)

        return NetworkOverviewResponse(
            total_nodes=len(nodes),
            total_edges=len(edges),
            states_covered=states,
            high_vulnerability_corridors=high_vul,
            average_elevation_m=avg_elev
        )


_network_service_instance = None

def get_network_service() -> NetworkGraphService:
    global _network_service_instance
    if _network_service_instance is None:
        _network_service_instance = NetworkGraphService()
    return _network_service_instance
