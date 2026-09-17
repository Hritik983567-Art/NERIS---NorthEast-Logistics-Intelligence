import time
import logging
from typing import Optional, List, Dict, Any

from app.adapters.base_adapter import BaseExternalAdapter
from app.data.ner_nodes_edges import build_ner_transportation_graph
from app.models.external_record import (
    AdapterFetchResult,
    ExternalRecord,
    RecordCategory,
    SeverityLevel,
    LocationMetadata
)

logger = logging.getLogger("ner_logitrack.adapters.road")

class RoadConditionAdapter(BaseExternalAdapter):
    def __init__(self):
        super().__init__(
            provider_name="NERIS NetworkX Dynamic Road Accessibility Engine",
            category=RecordCategory.ROAD_CONDITION,
            timeout_seconds=2.0
        )
        self.graph = build_ner_transportation_graph()

    async def fetch(self, state_filter: Optional[str] = None) -> AdapterFetchResult:
        retrieved_at = self.get_iso_timestamp()
        records: List[ExternalRecord] = []

        try:
            for u, v, data in self.graph.edges(data=True):
                hwy = data.get("highway_name", "NH-00")
                length_km = data.get("length_km", 50.0)
                profile = data.get("elevation_profile", "PLAINS")
                vul = data.get("vulnerability_index", 0.3)
                max_w = data.get("max_weight_tons", 30.0)
                u_node = self.graph.nodes[u]
                state = u_node.get("state", "Assam")

                if state_filter and state_filter.lower() != "all" and state.lower() != state_filter.lower():
                    continue

                severity = SeverityLevel.CRITICAL if vul >= 0.80 else (SeverityLevel.HIGH if vul >= 0.50 else SeverityLevel.INFO)
                status_desc = "EXPRESS CORRIDOR (CLEAR)" if vul < 0.40 else ("HIGH RISK GHAT (CAUTION)" if vul < 0.75 else "DISASTER VULNERABLE (HIGH BLOCKADE RISK)")

                records.append(ExternalRecord(
                    id=f"road-{u.lower()}-{v.lower()}",
                    category=RecordCategory.ROAD_CONDITION,
                    source="NERIS NetworkX Corridor Engine",
                    source_url="http://localhost:8000/api/v1/network/edges",
                    retrieved_at=retrieved_at,
                    published_at=retrieved_at,
                    title=f"Highway {hwy}: {u} ➔ {v} ({length_km} km)",
                    content_summary=f"Corridor {hwy} connecting {u} and {v}. Distance: {length_km} km. Elevation Profile: {profile}. Max Weight Limit: {max_w}T. Status: {status_desc}.",
                    location=LocationMetadata(
                        state=state,
                        highway_id=hwy,
                        hub_name=u,
                        lat=u_node.get("lat"),
                        lng=u_node.get("lng")
                    ),
                    severity=severity,
                    is_live=False,  # Marked False because calculated from standard spatial topology
                    extra_metadata={
                        "highway_name": hwy,
                        "length_km": length_km,
                        "elevation_profile": profile,
                        "vulnerability_index": vul,
                        "max_weight_tons": max_w
                    }
                ))
        except Exception as err:
            logger.warning(f"RoadConditionAdapter calculation error: {err}")
            return AdapterFetchResult(
                provider_name=self.provider_name,
                category=self.category,
                is_available=False,
                total_records=0,
                records=[],
                error_message=f"Road accessibility engine error: {str(err)}",
                retrieved_at=retrieved_at
            )

        return AdapterFetchResult(
            provider_name=self.provider_name,
            category=self.category,
            is_available=True,
            total_records=len(records),
            records=records,
            error_message=None,
            retrieved_at=retrieved_at
        )
