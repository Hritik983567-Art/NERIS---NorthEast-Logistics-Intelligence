import os
import json
import logging
from typing import Dict, Any, List, Optional
from app.models.historical_landslide_flood import (
    HistoricalLandslideFloodMetadata,
    HistoricalEventRecord,
    LandslideFloodAnalyticsResponse,
    EnvironmentalRiskIndexResponse,
    EnvironmentalRiskSummaryResponse,
    EnvironmentalRiskRegionDetailResponse,
    EnvironmentalRiskTrendsResponse
)

logger = logging.getLogger("neris.landslide_flood_service")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CACHE_PATH = os.path.join(BASE_DIR, "data", "historical_landslides_floods_db.json")
METADATA_PATH = os.path.join(BASE_DIR, "data", "historical_landslide_flood_metadata.json")

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

class LandslideFloodService:
    def __init__(self):
        self._data_cache: Optional[Dict[str, Any]] = None
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(CACHE_PATH):
            try:
                with open(CACHE_PATH, "r", encoding="utf-8") as f:
                    self._data_cache = json.load(f)
                logger.info(f"Loaded historical landslides/floods cache from {CACHE_PATH}")
            except Exception as e:
                logger.error(f"Error loading historical landslides/floods cache: {e}")
                self._data_cache = None

    def get_metadata(self) -> Dict[str, Any]:
        if self._data_cache and "metadata" in self._data_cache:
            meta = dict(self._data_cache["metadata"])
            meta["disclaimer"] = "HISTORICAL DATASET EVENT (source_type = 'historical_dataset') — NOT LIVE VERIFIED INCIDENT"
            return meta

        if os.path.exists(METADATA_PATH):
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["disclaimer"] = "HISTORICAL DATASET EVENT (source_type = 'historical_dataset') — NOT LIVE VERIFIED INCIDENT"
                return data

        return {
            "dataset_name": "Historical Landslide and Flood Event Catalog for India & North-East Region (2000–2023)",
            "source_organization": "NASA Global Landslide Catalog / Kaggle (sahilrajverma/landslide)",
            "kaggle_source_url": "https://www.kaggle.com/datasets/sahilrajverma/landslide",
            "license": "LICENSE VERIFICATION REQUIRED: Research & Educational License — Internal dataset for baseline risk analysis only.",
            "retrieval_date": "2026-09-13",
            "coverage_period": "2000–2023",
            "source_type": "historical_dataset",
            "data_type": "historical",
            "neris_operational_scope": NORTHEAST_STATES,
            "preprocessing_steps": ["Extracted NE events", "Validated columns", "Tagged with source_type = 'historical_dataset'"],
            "disclaimer": "HISTORICAL DATASET EVENT (source_type = 'historical_dataset') — NOT LIVE VERIFIED INCIDENT",
            "status": "VALIDATED_AND_DERIVED"
        }

    def get_analytics(self) -> Dict[str, Any]:
        if not self._data_cache:
            self._load_cache()
        if self._data_cache:
            return self._data_cache
        return {
            "metadata": self.get_metadata(),
            "events": [],
            "total_events_count": 0,
            "state_distribution": {st: 0 for st in NORTHEAST_STATES},
            "event_type_distribution": {"LANDSLIDE": 0, "FLOOD": 0},
            "severity_distribution": {"CRITICAL": 0, "HIGH": 0, "MODERATE": 0},
            "disclaimer": "HISTORICAL DATASET EVENT (source_type = 'historical_dataset') — NOT LIVE VERIFIED INCIDENT"
        }

    def get_summary(self) -> Dict[str, Any]:
        analytics = self.get_analytics()
        return {
            "total_events_count": analytics.get("total_events_count", 0),
            "state_distribution": analytics.get("state_distribution", {}),
            "event_type_distribution": analytics.get("event_type_distribution", {}),
            "severity_distribution": analytics.get("severity_distribution", {}),
            "state_risk_scores": analytics.get("state_environmental_risk_scores", {}),
            "data_type": "historical",
            "source_type": "historical_dataset",
            "disclaimer": "HISTORICAL FLOOD/LANDSLIDE RISK (source_type = 'historical_dataset', data_type = 'historical') — NOT LIVE DISASTER MONITORING",
            "metadata": self.get_metadata()
        }

    def get_risk_indices(self, state: Optional[str] = None) -> List[Dict[str, Any]]:
        analytics = self.get_analytics()
        scores = analytics.get("state_environmental_risk_scores", {})
        levels = analytics.get("state_environmental_risk_levels", {})
        ls_counts = analytics.get("state_landslide_exposure", {})
        fl_counts = analytics.get("state_flood_exposure", {})
        total_counts = analytics.get("state_distribution", {})

        results = []
        target_states = [s for s in NORTHEAST_STATES if state is None or s.lower() == state.strip().lower()]

        if state and not target_states:
            # Look for partial case-insensitive match
            target_states = [s for s in NORTHEAST_STATES if state.strip().lower() in s.lower()]

        for st in target_states:
            score = scores.get(st, 5.0)
            level = levels.get(st, "LOW")
            ls_c = ls_counts.get(st, 0)
            fl_c = fl_counts.get(st, 0)
            tot_c = total_counts.get(st, 0)

            results.append({
                "state": st,
                "environmental_risk_score": score,
                "risk_level": level,
                "landslide_count": ls_c,
                "flood_count": fl_c,
                "total_count": tot_c,
                "data_type": "historical",
                "source_type": "historical_dataset",
                "disclaimer": "HISTORICAL FLOOD/LANDSLIDE RISK (source_type = 'historical_dataset', data_type = 'historical') — NOT LIVE DISASTER MONITORING"
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
            # Fallback check
            for s in NORTHEAST_STATES:
                if st_clean in s.lower():
                    matched_state = s
                    break

        if not matched_state:
            return None

        analytics = self.get_analytics()
        events = analytics.get("events", [])
        state_events = [ev for ev in events if ev.get("state", "").lower() == matched_state.lower()]

        for ev in state_events:
            ev["source_type"] = "historical_dataset"
            ev["data_type"] = "historical"
            ev["disclaimer"] = "HISTORICAL DATASET EVENT (source_type = 'historical_dataset') — NOT LIVE VERIFIED INCIDENT"

        score = analytics.get("state_environmental_risk_scores", {}).get(matched_state, 5.0)
        level = analytics.get("state_environmental_risk_levels", {}).get(matched_state, "LOW")

        return {
            "state": matched_state,
            "environmental_risk_score": score,
            "risk_level": level,
            "total_events": len(state_events),
            "events": state_events,
            "data_type": "historical",
            "source_type": "historical_dataset",
            "disclaimer": "HISTORICAL FLOOD/LANDSLIDE RISK (source_type = 'historical_dataset', data_type = 'historical') — NOT LIVE DISASTER MONITORING"
        }

    def get_trends(self, start_year: Optional[int] = None, end_year: Optional[int] = None) -> Dict[str, Any]:
        analytics = self.get_analytics()
        events = analytics.get("events", [])

        yearly_dist: Dict[str, int] = {}
        monthly_dist: Dict[str, int] = {f"{m:02d}": 0 for m in range(1, 13)}
        type_trends: Dict[str, Dict[str, int]] = {}

        for ev in events:
            yr = ev.get("year", 2000)
            if start_year and yr < start_year:
                continue
            if end_year and yr > end_year:
                continue

            yr_str = str(yr)
            yearly_dist[yr_str] = yearly_dist.get(yr_str, 0) + 1

            ev_date = str(ev.get("event_date", ""))
            if len(ev_date) >= 7 and "-" in ev_date:
                month_str = ev_date.split("-")[1]
                if month_str in monthly_dist:
                    monthly_dist[month_str] += 1

            ev_type = str(ev.get("normalized_event_type", ev.get("event_type", "OTHER"))).upper()
            if ev_type not in type_trends:
                type_trends[ev_type] = {}
            type_trends[ev_type][yr_str] = type_trends[ev_type].get(yr_str, 0) + 1

        return {
            "yearly_distribution": dict(sorted(yearly_dist.items())),
            "monthly_distribution": monthly_dist,
            "event_type_trends": type_trends,
            "data_type": "historical",
            "source_type": "historical_dataset",
            "disclaimer": "HISTORICAL FLOOD/LANDSLIDE RISK (source_type = 'historical_dataset', data_type = 'historical') — NOT LIVE DISASTER MONITORING"
        }

    def get_historical_records(self, event_type: Optional[str] = None, state: Optional[str] = None) -> List[Dict[str, Any]]:
        analytics = self.get_analytics()
        events = analytics.get("events", [])

        filtered = []
        for ev in events:
            ev["source_type"] = "historical_dataset"
            ev["data_type"] = "historical"
            ev["disclaimer"] = "HISTORICAL DATASET EVENT (source_type = 'historical_dataset') — NOT LIVE VERIFIED INCIDENT"

            if event_type:
                et_str = event_type.strip().upper()
                if et_str not in str(ev.get("event_type", "")).upper() and et_str not in str(ev.get("normalized_event_type", "")).upper():
                    continue

            if state:
                st_str = state.strip().lower()
                if st_str not in str(ev.get("state", "")).lower():
                    continue

            filtered.append(ev)
        return filtered

    def get_corridor_historical_exposure_penalties(self, from_node: str, to_node: str) -> Dict[str, float]:
        st1 = HUB_STATE_MAP.get(from_node, "Assam")
        st2 = HUB_STATE_MAP.get(to_node, "Assam")

        analytics = self.get_analytics()
        ls_exp = analytics.get("state_landslide_exposure", {})
        fl_exp = analytics.get("state_flood_exposure", {})

        ls_count = (ls_exp.get(st1, 0) + ls_exp.get(st2, 0)) / 2.0
        fl_count = (fl_exp.get(st1, 0) + fl_exp.get(st2, 0)) / 2.0

        flood_penalty = round(1.0 + min(0.25, fl_count * 0.08), 3)
        landslide_penalty = round(1.0 + min(0.30, ls_count * 0.10), 3)

        return {
            "historical_flood_penalty": flood_penalty,
            "historical_landslide_penalty": landslide_penalty
        }

_landslide_flood_service_instance = None

def get_landslide_flood_service() -> LandslideFloodService:
    global _landslide_flood_service_instance
    if _landslide_flood_service_instance is None:
        _landslide_flood_service_instance = LandslideFloodService()
    return _landslide_flood_service_instance

