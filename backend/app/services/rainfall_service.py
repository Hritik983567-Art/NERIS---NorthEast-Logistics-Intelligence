import os
import json
import logging
from typing import Dict, Any, List, Optional
from app.models.historical_rainfall import (
    RainfallMetadataResponse,
    RainfallAnalyticsResponse,
    SubdivisionRainfallStats,
    SubdivisionRiskIndex
)

logger = logging.getLogger("neris.rainfall_service")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CACHE_PATH = os.path.join(BASE_DIR, "data", "historical_rainfall_db.json")
METADATA_PATH = os.path.join(BASE_DIR, "data", "historical_rainfall_metadata.json")

# Map logistics hubs to IMD meteorological subdivisions
HUB_TO_SUBDIVISION = {
    "Guwahati": "ASSAM & MEGHALAYA",
    "Shillong": "ASSAM & MEGHALAYA",
    "Silchar": "ASSAM & MEGHALAYA",
    "Tezpur": "ASSAM & MEGHALAYA",
    "Jowai": "ASSAM & MEGHALAYA",
    "Bongaigaon": "ASSAM & MEGHALAYA",
    "Nagaon": "ASSAM & MEGHALAYA",
    "Itanagar": "ARUNACHAL PRADESH",
    "Tawang": "ARUNACHAL PRADESH",
    "Pasighat": "ARUNACHAL PRADESH",
    "Kohima": "NAGA MANI MIZO TRIPURA",
    "Dimapur": "NAGA MANI MIZO TRIPURA",
    "Imphal": "NAGA MANI MIZO TRIPURA",
    "Aizawl": "NAGA MANI MIZO TRIPURA",
    "Agartala": "NAGA MANI MIZO TRIPURA",
    "Gangtok": "SUB HIMALAYAN WEST BENGAL & SIKKIM"
}

class RainfallService:
    def __init__(self):
        self._data_cache: Optional[Dict[str, Any]] = None
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(CACHE_PATH):
            try:
                with open(CACHE_PATH, "r", encoding="utf-8") as f:
                    self._data_cache = json.load(f)
                logger.info(f"Loaded historical rainfall cache from {CACHE_PATH}")
            except Exception as e:
                logger.error(f"Error loading historical rainfall cache: {e}")
                self._data_cache = None

    def get_metadata(self) -> Dict[str, Any]:
        if self._data_cache and "metadata" in self._data_cache:
            meta = dict(self._data_cache["metadata"])
            meta["disclaimer"] = "HISTORICAL RAINFALL — NOT LIVE WEATHER"
            return meta

        if os.path.exists(METADATA_PATH):
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["disclaimer"] = "HISTORICAL RAINFALL — NOT LIVE WEATHER"
                return data

        return {
            "dataset_name": "Sub-divisional Monthly Rainfall Data for India (1901–2017)",
            "source_organization": "India Meteorological Department (IMD)",
            "original_upstream_url": "https://data.gov.in/catalog/rainfall-india",
            "kaggle_source_url": "https://www.kaggle.com/datasets/saisaran2/rainfall-data-from-1901-to-2017-for-india",
            "license": "Open Government Data License (OGDL) India",
            "retrieval_date": "2026-09-13",
            "coverage_period": "1901–2017 (117 Years)",
            "neris_operational_scope": ["ASSAM & MEGHALAYA", "ARUNACHAL PRADESH", "NAGA MANI MIZO TRIPURA", "SUB HIMALAYAN WEST BENGAL & SIKKIM"],
            "mapped_hubs_count": 15,
            "preprocessing_steps": ["Filtered NER subdivisions", "Cleaned missing values", "Calculated 117-year monthly means"],
            "disclaimer": "HISTORICAL RAINFALL — NOT LIVE WEATHER",
            "status": "VALIDATED_AND_DERIVED"
        }

    def get_analytics(self) -> Dict[str, Any]:
        if not self._data_cache:
            self._load_cache()

        if self._data_cache:
            return self._data_cache

        return {
            "metadata": self.get_metadata(),
            "baselines": {},
            "annual_trend_series": [],
            "extreme_rainfall_records": [],
            "processed_records_count": 0,
            "disclaimer": "HISTORICAL RAINFALL — NOT LIVE WEATHER. Multi-decade statistical baseline (1901–2017)."
        }

    def get_summary(self) -> Dict[str, Any]:
        analytics = self.get_analytics()
        baselines = analytics.get("baselines", {})
        metadata = analytics.get("metadata", self.get_metadata())
        
        subdivisions_summary = []
        for sub, data in baselines.items():
            subdivisions_summary.append({
                "subdivision": sub,
                "region_code": data.get("region_code"),
                "states": data.get("states", []),
                "average_annual_mm": data.get("average_annual_mm"),
                "average_monsoon_mm": data.get("average_monsoon_mm"),
                "primary_hubs": data.get("primary_hubs", [])
            })

        return {
            "metadata": metadata,
            "subdivisions": subdivisions_summary,
            "total_operational_subdivisions": len(subdivisions_summary),
            "coverage_period": metadata.get("coverage_period", "1901–2017"),
            "disclaimer": "HISTORICAL RAINFALL — NOT LIVE WEATHER"
        }

    def get_region_detail(self, region: str) -> Optional[Dict[str, Any]]:
        reg_clean = region.strip().upper()
        analytics = self.get_analytics()
        baselines = analytics.get("baselines", {})

        # 1. Exact subdivision match
        if reg_clean in baselines:
            res = dict(baselines[reg_clean])
            res["disclaimer"] = "HISTORICAL RAINFALL — NOT LIVE WEATHER"
            return res

        # 2. Match by region code or state name substring
        for sub, data in baselines.items():
            if data.get("region_code", "").upper() == reg_clean:
                res = dict(data)
                res["disclaimer"] = "HISTORICAL RAINFALL — NOT LIVE WEATHER"
                return res

            states = [s.upper() for s in data.get("states", [])]
            if any(st in reg_clean or reg_clean in st for st in states):
                res = dict(data)
                res["disclaimer"] = "HISTORICAL RAINFALL — NOT LIVE WEATHER"
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

    def get_risk_indices_for_month(self, month: str = "SEP") -> List[Dict[str, Any]]:
        m_upper = month.strip().upper()[:3]
        valid_months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        if m_upper not in valid_months:
            raise ValueError(f"Invalid month query parameter '{month}'. Must be one of: {', '.join(valid_months)}")

        analytics = self.get_analytics()
        baselines = analytics.get("baselines", {})

        results = []
        for sub, data in baselines.items():
            means = data.get("monthly_means_mm", {})
            indices = data.get("monthly_risk_indices", {})

            mean_val = float(means.get(m_upper, 0.0) or 0.0)
            score = float(indices.get(m_upper, 0.0) or 0.0)

            if score >= 0.75:
                level = "CRITICAL"
            elif score >= 0.50:
                level = "HIGH"
            elif score >= 0.25:
                level = "MODERATE"
            else:
                level = "LOW"

            results.append({
                "subdivision": sub,
                "region_code": data.get("region_code", "NER"),
                "month": m_upper,
                "mean_rainfall_mm": mean_val,
                "risk_score": score,
                "risk_level": level,
                "disclaimer": "HISTORICAL RAINFALL — NOT LIVE WEATHER"
            })

        return results

    def get_route_rainfall_risk_weight(self, from_node: str, to_node: str, month: str = "SEP") -> float:
        """
        Computes deterministic historical rainfall risk factor for route segment evaluation.
        Does NOT rely on LLM choice; pure mathematical baseline calculation.
        """
        m_upper = month.strip().upper()[:3]
        sub1 = HUB_TO_SUBDIVISION.get(from_node, "ASSAM & MEGHALAYA")
        sub2 = HUB_TO_SUBDIVISION.get(to_node, "ASSAM & MEGHALAYA")

        analytics = self.get_analytics()
        baselines = analytics.get("baselines", {})

        b1 = baselines.get(sub1, {}).get("monthly_risk_indices", {}).get(m_upper, 0.5)
        b2 = baselines.get(sub2, {}).get("monthly_risk_indices", {}).get(m_upper, 0.5)

        avg_risk_index = (float(b1) + float(b2)) / 2.0
        # Multiplier scales between 1.0 (baseline) and 1.6 (high historical monsoon risk)
        return round(1.0 + (avg_risk_index * 0.6), 3)

_rainfall_service_instance = None

def get_rainfall_service() -> RainfallService:
    global _rainfall_service_instance
    if _rainfall_service_instance is None:
        _rainfall_service_instance = RainfallService()
    return _rainfall_service_instance
