import os
import json
import logging
from typing import Dict, Any, List, Optional
from app.models.emergency_resource import (
    EmergencyResourceMetadata,
    EmergencyResourceRecord,
    EmergencyResourceSummaryResponse,
    EmergencyResourceCoverageResponse,
    EmergencyResourceRegionDetailResponse,
    EmergencyResourceTrendsResponse
)

logger = logging.getLogger("neris.emergency_resource_service")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CACHE_PATH = os.path.join(BASE_DIR, "data", "emergency_resources_db.json")
METADATA_PATH = os.path.join(BASE_DIR, "data", "emergency_resources_metadata.json")

NORTHEAST_STATES = [
    "Arunachal Pradesh", "Assam", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Sikkim", "Tripura"
]

HUB_STATE_MAP = {
    "Guwahati": "Assam", "Silchar": "Assam", "Tezpur": "Assam", "Nagaon": "Assam", "Bongaigaon": "Assam",
    "Shillong": "Meghalaya", "Jowai": "Meghalaya",
    "Itanagar": "Arunachal Pradesh", "Tawang": "Arunachal Pradesh", "Pasighat": "Arunachal Pradesh",
    "Kohima": "Nagaland", "Dimapur": "Nagaland",
    "Imphal": "Manipur",
    "Aizawl": "Mizoram",
    "Agartala": "Tripura",
    "Gangtok": "Sikkim"
}

class EmergencyResourceService:
    def __init__(self):
        self._data_cache: Optional[Dict[str, Any]] = None
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(CACHE_PATH):
            try:
                with open(CACHE_PATH, "r", encoding="utf-8") as f:
                    self._data_cache = json.load(f)
                logger.info(f"Loaded Dataset 4 emergency resources cache from {CACHE_PATH}")
            except Exception as e:
                logger.error(f"Error loading Dataset 4 emergency resources cache: {e}")
                self._data_cache = None

    def get_metadata(self) -> Dict[str, Any]:
        if self._data_cache and "metadata" in self._data_cache:
            meta = dict(self._data_cache["metadata"])
            meta["disclaimer"] = "HISTORICAL RESOURCE DATA (source_type = 'historical_dataset', data_type = 'historical') — NOT LIVE AVAILABILITY"
            return meta

        if os.path.exists(METADATA_PATH):
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["disclaimer"] = "HISTORICAL RESOURCE DATA (source_type = 'historical_dataset', data_type = 'historical') — NOT LIVE AVAILABILITY"
                return data

        return {
            "dataset_name": "Emergency Resource Allocation Intelligence Data",
            "source_organization": "Kaggle (programmer3/emergency-resource-allocation-intelligence-data)",
            "kaggle_source_url": "https://www.kaggle.com/datasets/programmer3/emergency-resource-allocation-intelligence-data/data",
            "license": "CC0: Public Domain / Open Research Dataset",
            "license_verified": True,
            "retrieval_date": "2026-09-13",
            "coverage_period": "2022–2026",
            "source_type": "historical_dataset",
            "data_type": "historical",
            "neris_operational_scope": NORTHEAST_STATES,
            "resource_categories": ["HOSPITAL", "WAREHOUSE", "SHELTER", "TRANSPORT"],
            "preprocessing_steps": ["Validated resource fields", "Tagged with source_type = 'historical_dataset'"],
            "disclaimer": "HISTORICAL RESOURCE DATA (source_type = 'historical_dataset', data_type = 'historical') — NOT LIVE AVAILABILITY",
            "status": "VALIDATED_AND_DERIVED"
        }

    def get_analytics(self) -> Dict[str, Any]:
        if not self._data_cache:
            self._load_cache()
        if self._data_cache:
            return self._data_cache
        return {
            "metadata": self.get_metadata(),
            "resources": [],
            "total_resources_count": 0,
            "state_distribution": {st: 0 for st in NORTHEAST_STATES},
            "type_distribution": {"HOSPITAL": 0, "WAREHOUSE": 0, "SHELTER": 0, "TRANSPORT": 0},
            "state_capacity": {st: 0 for st in NORTHEAST_STATES},
            "state_coverage_scores": {st: 10.0 for st in NORTHEAST_STATES},
            "state_coverage_levels": {st: "CRITICAL_DEFICIT" for st in NORTHEAST_STATES},
            "data_type": "historical",
            "source_type": "historical_dataset",
            "disclaimer": "HISTORICAL RESOURCE DATA — NOT LIVE AVAILABILITY"
        }

    def get_summary(self) -> Dict[str, Any]:
        analytics = self.get_analytics()
        tot_res = analytics.get("total_resources_count", 0)
        tot_cap = sum(analytics.get("state_capacity", {}).values())
        cov_scores = list(analytics.get("state_coverage_scores", {}).values())
        avg_score = round(sum(cov_scores) / max(1, len(cov_scores)), 1) if cov_scores else 50.0

        return {
            "total_resources": tot_res,
            "total_resources_count": tot_res,
            "total_capacity": tot_cap,
            "average_coverage_score": avg_score,
            "state_distribution": analytics.get("state_distribution", {}),
            "type_distribution": analytics.get("type_distribution", {}),
            "state_capacity": analytics.get("state_capacity", {}),
            "state_coverage_scores": analytics.get("state_coverage_scores", {}),
            "data_type": "historical",
            "source_type": "historical_dataset",
            "disclaimer": "HISTORICAL RESOURCE DATA (source_type = 'historical_dataset', data_type = 'historical') — NOT LIVE AVAILABILITY",
            "metadata": self.get_metadata()
        }

    def get_by_region(self, state: str) -> Optional[Dict[str, Any]]:
        return self.get_region_detail(state)

    def calculate_resource_coverage_score(self, state: str) -> float:
        analytics = self.get_analytics()
        scores = analytics.get("state_coverage_scores", {})
        return float(scores.get(state, 50.0))

    def get_types(self) -> Dict[str, Any]:
        analytics = self.get_analytics()
        type_dist = analytics.get("type_distribution", {})
        return {
            "categories": list(type_dist.keys()),
            "type_distribution": type_dist,
            "data_type": "historical",
            "source_type": "historical_dataset",
            "disclaimer": "HISTORICAL RESOURCE DATA — NOT LIVE AVAILABILITY"
        }

    def get_resources(self, resource_type: Optional[str] = None, state: Optional[str] = None) -> List[Dict[str, Any]]:
        analytics = self.get_analytics()
        resources = analytics.get("resources", [])

        filtered = []
        for res in resources:
            res["source_type"] = "historical_dataset"
            res["data_type"] = "historical"
            res["disclaimer"] = "HISTORICAL RESOURCE DATA (source_type = 'historical_dataset', data_type = 'historical') — NOT LIVE AVAILABILITY"

            if resource_type:
                rt_str = resource_type.strip().upper()
                if rt_str not in str(res.get("type", "")).upper() and rt_str not in str(res.get("source_resource_type", "")).upper():
                    continue

            if state:
                st_str = state.strip().lower()
                if st_str not in str(res.get("state", "")).lower():
                    continue

            filtered.append(res)
        return filtered

    def get_resource_by_id(self, resource_id: str) -> Optional[Dict[str, Any]]:
        if not resource_id or not resource_id.strip():
            return None
        res_clean = resource_id.strip().upper()
        analytics = self.get_analytics()
        resources = analytics.get("resources", [])

        for res in resources:
            if str(res.get("id", "")).upper() == res_clean or str(res.get("resource_id", "")).upper() == res_clean:
                res["source_type"] = "historical_dataset"
                res["data_type"] = "historical"
                res["disclaimer"] = "HISTORICAL RESOURCE DATA (source_type = 'historical_dataset', data_type = 'historical') — NOT LIVE AVAILABILITY"
                return res
        return None

    def get_coverage(self, state: Optional[str] = None) -> List[Dict[str, Any]]:
        analytics = self.get_analytics()
        scores = analytics.get("state_coverage_scores", {})
        levels = analytics.get("state_coverage_levels", {})
        counts = analytics.get("state_distribution", {})
        capacities = analytics.get("state_capacity", {})

        results = []
        target_states = [s for s in NORTHEAST_STATES if state is None or s.lower() == state.strip().lower()]

        if state and not target_states:
            target_states = [s for s in NORTHEAST_STATES if state.strip().lower() in s.lower()]

        for st in target_states:
            score = scores.get(st, 10.0)
            level = levels.get(st, "CRITICAL_DEFICIT")
            cnt = counts.get(st, 0)
            cap = capacities.get(st, 0)

            results.append({
                "state": st,
                "resource_coverage_score": score,
                "coverage_level": level,
                "total_resources": cnt,
                "total_capacity": cap,
                "data_type": "historical",
                "source_type": "historical_dataset",
                "disclaimer": "HISTORICAL RESOURCE DATA (source_type = 'historical_dataset', data_type = 'historical') — NOT LIVE AVAILABILITY"
            })
        return results

    def get_region_detail(self, state: str) -> Optional[Dict[str, Any]]:
        st_clean = state.strip().lower()
        matched_state = None
        for s in NORTHEAST_STATES:
            if s.lower() == st_clean:
                matched_state = s
                break
        if not matched_state:
            for s in NORTHEAST_STATES:
                if st_clean in s.lower():
                    matched_state = s
                    break

        if not matched_state:
            return None

        analytics = self.get_analytics()
        resources = analytics.get("resources", [])
        state_resources = [r for r in resources if r.get("state", "").lower() == matched_state.lower()]

        for r in state_resources:
            r["source_type"] = "historical_dataset"
            r["data_type"] = "historical"
            r["disclaimer"] = "HISTORICAL RESOURCE DATA (source_type = 'historical_dataset', data_type = 'historical') — NOT LIVE AVAILABILITY"

        score = analytics.get("state_coverage_scores", {}).get(matched_state, 10.0)
        level = analytics.get("state_coverage_levels", {}).get(matched_state, "CRITICAL_DEFICIT")
        total_cap = analytics.get("state_capacity", {}).get(matched_state, 0)

        return {
            "state": matched_state,
            "resource_coverage_score": score,
            "coverage_level": level,
            "total_resources": len(state_resources),
            "total_capacity": total_cap,
            "resources": state_resources,
            "data_type": "historical",
            "source_type": "historical_dataset",
            "disclaimer": "HISTORICAL RESOURCE DATA (source_type = 'historical_dataset', data_type = 'historical') — NOT LIVE AVAILABILITY"
        }

    def get_trends(self, start_year: Optional[int] = None, end_year: Optional[int] = None) -> Dict[str, Any]:
        analytics = self.get_analytics()
        resources = analytics.get("resources", [])

        yearly_dist: Dict[str, int] = {}
        type_trends: Dict[str, Dict[str, int]] = {}

        for r in resources:
            last_up = str(r.get("last_updated", "2026"))
            yr = 2026
            if len(last_up) >= 4 and last_up[:4].isdigit():
                yr = int(last_up[:4])

            if start_year and yr < start_year:
                continue
            if end_year and yr > end_year:
                continue

            yr_str = str(yr)
            yearly_dist[yr_str] = yearly_dist.get(yr_str, 0) + 1

            rtype = str(r.get("type", "OTHER")).upper()
            if rtype not in type_trends:
                type_trends[rtype] = {}
            type_trends[rtype][yr_str] = type_trends[rtype].get(yr_str, 0) + 1

        return {
            "yearly_distribution": dict(sorted(yearly_dist.items())),
            "type_trends": type_trends,
            "data_type": "historical",
            "source_type": "historical_dataset",
            "disclaimer": "HISTORICAL RESOURCE DATA (source_type = 'historical_dataset', data_type = 'historical') — NOT LIVE AVAILABILITY"
        }

    def get_corridor_historical_resource_accessibility(self, from_node: str, to_node: str) -> Dict[str, float]:
        """
        Computes deterministic historical emergency resource accessibility multiplier for NetworkX Dijkstra solver.
        Regions with lower historical emergency resource density/coverage incur a modest multiplier penalty (1.0x to 1.15x).
        Bedrock is NEVER allowed to choose or alter the route.
        """
        st1 = HUB_STATE_MAP.get(from_node, "Assam")
        st2 = HUB_STATE_MAP.get(to_node, "Assam")

        analytics = self.get_analytics()
        scores = analytics.get("state_coverage_scores", {})

        sc1 = scores.get(st1, 50.0)
        sc2 = scores.get(st2, 50.0)
        avg_score = (sc1 + sc2) / 2.0

        # Deterministic formula: Lower score -> slightly higher routing multiplier (max 1.15x)
        resource_penalty = round(1.0 + max(0.0, min(0.15, (100.0 - avg_score) * 0.0015)), 3)

        return {
            "historical_resource_accessibility_penalty": resource_penalty
        }

    def get_corridor_resource_penalty(self, from_node: str, to_node: str) -> float:
        res = self.get_corridor_historical_resource_accessibility(from_node, to_node)
        return float(res.get("historical_resource_accessibility_penalty", 1.0))

_emergency_resource_service_instance = None

def get_emergency_resource_service() -> EmergencyResourceService:
    global _emergency_resource_service_instance
    if _emergency_resource_service_instance is None:
        _emergency_resource_service_instance = EmergencyResourceService()
    return _emergency_resource_service_instance
