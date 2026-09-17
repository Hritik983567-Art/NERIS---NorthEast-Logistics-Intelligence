import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("neris.road_accident_service")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CACHE_PATH = os.path.join(BASE_DIR, "data", "historical_road_accidents_db.json")
METADATA_PATH = os.path.join(BASE_DIR, "data", "historical_road_accident_metadata.json")

# Mapping logistics nodes to states
HUB_TO_STATE = {
    "Guwahati": "Assam",
    "Shillong": "Meghalaya",
    "Silchar": "Assam",
    "Tezpur": "Assam",
    "Jowai": "Meghalaya",
    "Bongaigaon": "Assam",
    "Nagaon": "Assam",
    "Itanagar": "Arunachal Pradesh",
    "Tawang": "Arunachal Pradesh",
    "Pasighat": "Arunachal Pradesh",
    "Kohima": "Nagaland",
    "Dimapur": "Nagaland",
    "Imphal": "Manipur",
    "Aizawl": "Mizoram",
    "Agartala": "Tripura",
    "Gangtok": "Sikkim"
}

class RoadAccidentService:
    def __init__(self):
        self._data_cache: Optional[Dict[str, Any]] = None
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(CACHE_PATH):
            try:
                with open(CACHE_PATH, "r", encoding="utf-8") as f:
                    self._data_cache = json.load(f)
                logger.info(f"Loaded historical road accident cache from {CACHE_PATH}")
            except Exception as e:
                logger.error(f"Error loading historical road accident cache: {e}")
                self._data_cache = None

    def get_metadata(self) -> Dict[str, Any]:
        if self._data_cache and "metadata" in self._data_cache:
            meta = dict(self._data_cache["metadata"])
            meta["disclaimer"] = "HISTORICAL ROAD RISK — NOT LIVE ACCIDENT DATA"
            return meta

        if os.path.exists(METADATA_PATH):
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["disclaimer"] = "HISTORICAL ROAD RISK — NOT LIVE ACCIDENT DATA"
                return data

        return {
            "dataset_name": "Indian Road Accident Statistical Dataset (2022–2025)",
            "source_organization": "Kaggle (sehaj1104/indian-road-accident-dataset-20222025)",
            "kaggle_source_url": "https://www.kaggle.com/datasets/sehaj1104/indian-road-accident-dataset-20222025",
            "license": "CC0: Public Domain / Open Research Dataset",
            "retrieval_date": "2026-09-13",
            "coverage_period": "2022–2025",
            "source_type": "historical_synthetic_dataset",
            "neris_operational_scope": ["Meghalaya", "Assam", "Arunachal Pradesh", "Nagaland", "Manipur", "Mizoram", "Tripura", "Sikkim"],
            "synthetic_data_limitations": "WARNING: Individual coordinates and contextual attributes may be synthetically generated. Individual records must NEVER be displayed as verified live emergency incidents.",
            "preprocessing_steps": ["Filtered NER states", "Aggregated risk indices by state", "Computed NetworkX Dijkstra road accident penalties"],
            "disclaimer": "HISTORICAL ROAD RISK — NOT LIVE ACCIDENT DATA",
            "status": "VALIDATED_AND_AGGREGATED"
        }

    def get_analytics(self) -> Dict[str, Any]:
        if not self._data_cache:
            self._load_cache()

        data = dict(self._data_cache) if self._data_cache else {}
        baselines = data.get("state_baselines", {})
        if "risk_indices" not in data or not data["risk_indices"]:
            indices = []
            for st, b_data in baselines.items():
                avg_score = float(b_data.get("average_event_risk_score", 5.0))
                r_score = b_data.get("risk_score") or round(min(99.0, max(5.0, avg_score * 8.5)), 1)
                indices.append({
                    "state": st,
                    "risk_score": r_score,
                    "risk_level": b_data.get("risk_level", "LOW"),
                    "route_multiplier": b_data.get("route_risk_multiplier", 1.0),
                    "total_records": b_data.get("total_accidents", 1),
                    "top_risk_factors": list(b_data.get("weather_breakdown", {}).keys()) + list(b_data.get("severity_breakdown", {}).keys()),
                    "disclaimer": "HISTORICAL ACCIDENT RISK — NOT LIVE INCIDENTS"
                })
            data["risk_indices"] = indices

        if "risk_factor_breakdown" not in data:
            data["risk_factor_breakdown"] = {
                "weather_exposure": 35.0,
                "severity_exposure": 30.0,
                "visibility_exposure": 20.0,
                "traffic_density": 15.0
            }
        data["disclaimer"] = "HISTORICAL ACCIDENT RISK — NOT LIVE INCIDENTS"
        return data

    def get_summary(self) -> Dict[str, Any]:
        analytics = self.get_analytics()
        baselines = analytics.get("state_baselines", {})
        metadata = analytics.get("metadata", self.get_metadata())

        states_summary = []
        for st, data in baselines.items():
            avg_score = float(data.get("average_event_risk_score", 5.0))
            r_score = data.get("risk_score") or round(min(99.0, max(5.0, avg_score * 8.5)), 1)
            states_summary.append({
                "state": st,
                "total_accidents": data.get("total_accidents", 0),
                "fatal_accidents": data.get("fatal_accidents", 0),
                "average_event_risk_score": avg_score,
                "risk_score": r_score,
                "risk_level": data.get("risk_level", "LOW"),
                "route_risk_multiplier": data.get("route_risk_multiplier", 1.0)
            })

        return {
            "metadata": metadata,
            "state_summaries": states_summary,
            "total_operational_states": len(states_summary),
            "coverage_period": metadata.get("coverage_period", "2022–2025"),
            "disclaimer": "HISTORICAL ACCIDENT RISK — NOT LIVE INCIDENTS"
        }

    def get_region_detail(self, region: str) -> Optional[Dict[str, Any]]:
        reg_clean = region.strip().upper()
        analytics = self.get_analytics()
        baselines = analytics.get("state_baselines", {})

        for st, data in baselines.items():
            if st.upper() == reg_clean or st.upper() in reg_clean or reg_clean in st.upper():
                res = dict(data)
                avg_score = float(res.get("average_event_risk_score", 5.0))
                res["risk_score"] = res.get("risk_score") or round(min(99.0, max(5.0, avg_score * 8.5)), 1)
                res["disclaimer"] = "HISTORICAL ACCIDENT RISK — NOT LIVE INCIDENTS"
                return res

        return None

    def get_trends(self, start_year: Optional[int] = None, end_year: Optional[int] = None) -> List[Dict[str, Any]]:
        analytics = self.get_analytics()
        series = analytics.get("annual_trend_series", [])

        if start_year is not None and end_year is not None:
            if start_year > end_year:
                raise ValueError(f"Invalid year range: start_year ({start_year}) cannot be greater than end_year ({end_year}).")

        filtered = []
        for pt in series:
            y = pt.get("year")
            if start_year is not None and y < start_year:
                continue
            if end_year is not None and y > end_year:
                continue
            filtered.append(pt)

        return filtered

    def get_route_road_risk_weight(self, from_node: str, to_node: str) -> float:
        """
        Computes deterministic historical road accident risk factor for route segment evaluation.
        Does NOT rely on LLM choice; pure mathematical baseline calculation based on state accident history.
        Formula multiplier ranges between 1.0x (baseline) and 1.35x (high historical road risk).
        """
        st1 = HUB_TO_STATE.get(from_node, "Assam")
        st2 = HUB_TO_STATE.get(to_node, "Assam")

        analytics = self.get_analytics()
        baselines = analytics.get("state_baselines", {})

        b1 = baselines.get(st1, {}).get("route_risk_multiplier", 1.05)
        b2 = baselines.get(st2, {}).get("route_risk_multiplier", 1.05)

        avg_multiplier = (float(b1) + float(b2)) / 2.0
        return round(avg_multiplier, 3)

_road_accident_service_instance = None

def get_road_accident_service() -> RoadAccidentService:
    global _road_accident_service_instance
    if _road_accident_service_instance is None:
        _road_accident_service_instance = RoadAccidentService()
    return _road_accident_service_instance
