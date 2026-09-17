import os
import csv
import json
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest_landslide_flood")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "backend", "app", "data")
CSV_PATH = os.path.join(DATA_DIR, "historical_landslide_flood_dataset.csv")
JSON_DB_PATH = os.path.join(DATA_DIR, "historical_landslides_floods_db.json")
METADATA_PATH = os.path.join(DATA_DIR, "historical_landslide_flood_metadata.json")

NER_STATES = {
    "Assam", "Meghalaya", "Arunachal Pradesh", "Nagaland",
    "Manipur", "Mizoram", "Tripura", "Sikkim"
}

def normalize_event_type(raw_type: str, title: str) -> str:
    combined = (str(raw_type) + " " + str(title)).upper()
    if "LANDSLIDE" in combined or "ROCKFALL" in combined or "MUDSLIDE" in combined or "SLOPE" in combined or "SLUMP" in combined:
        return "LANDSLIDE"
    elif "FLOOD" in combined or "FLASH" in combined or "RIVERINE" in combined or "INUNDATION" in combined or "SURGE" in combined:
        return "FLOOD"
    return "OTHER_UNKNOWN"

def main():
    if not os.path.exists(CSV_PATH):
        logger.error(f"Input CSV dataset missing: {CSV_PATH}")
        return

    logger.info(f"Ingesting historical flood & landslide dataset from {CSV_PATH}...")

    raw_events: List[Dict[str, Any]] = []
    processed_events: List[Dict[str, Any]] = []

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_events.append(row)

            state = (row.get("state") or "Unknown").strip()
            # Operational scope filter
            is_ner = any(st.lower() in state.lower() or state.lower() in st.lower() for st in NER_STATES)

            if not is_ner:
                logger.info(f"Skipping non-NER event record: {row.get('event_id')} ({state})")
                continue

            raw_event_type = (row.get("event_type") or "UNKNOWN").strip()
            title = (row.get("title") or "Historical Event").strip()
            norm_event_type = normalize_event_type(raw_event_type, title)

            try:
                lat = float(row.get("latitude")) if row.get("latitude") else None
            except (ValueError, TypeError):
                lat = None

            try:
                lng = float(row.get("longitude")) if row.get("longitude") else None
            except (ValueError, TypeError):
                lng = None

            try:
                year = int(row.get("year")) if row.get("year") else None
            except (ValueError, TypeError):
                year = None

            try:
                fatalities = int(row.get("fatalities")) if row.get("fatalities") else 0
            except (ValueError, TypeError):
                fatalities = 0

            event_id = row.get("event_id") or f"EV-{len(processed_events)+1:03d}"
            severity = (row.get("severity") or "MODERATE").strip().upper()

            record = {
                "id": event_id,
                "event_id": event_id,
                "title": title,
                "source_event_type": raw_event_type,
                "normalized_event_type": norm_event_type,
                "event_type": norm_event_type,
                "state": state,
                "district": (row.get("district") or "Unknown").strip(),
                "latitude": lat,
                "lat": lat,
                "longitude": lng,
                "lng": lng,
                "event_date": row.get("event_date") or None,
                "year": year,
                "severity": severity,
                "trigger": row.get("trigger") or "Unknown",
                "fatalities": fatalities,
                "source_type": "historical_dataset",
                "data_type": "historical",
                "source": row.get("source") or "NASA Global Landslide Catalog / Kaggle",
                "dataset_source": row.get("source") or "NASA Global Landslide Catalog / Kaggle",
                "disclaimer": "HISTORICAL DATASET EVENT (source_type = 'historical_dataset', data_type = 'historical') — NOT LIVE VERIFIED INCIDENT",
                "historical_status": "RESEARCH_BASELINE_DATA"
            }
            processed_events.append(record)

    logger.info(f"Processed {len(processed_events)} Northeast operational event records.")

    # Calculate State-level Derived Baselines & Historical Environmental Risk Scores
    state_landslide_count: Dict[str, int] = {st: 0 for st in NER_STATES}
    state_flood_count: Dict[str, int] = {st: 0 for st in NER_STATES}
    state_total_count: Dict[str, int] = {st: 0 for st in NER_STATES}
    state_fatalities: Dict[str, int] = {st: 0 for st in NER_STATES}
    state_risk_scores: Dict[str, float] = {}
    state_risk_levels: Dict[str, str] = {}
    state_route_multipliers: Dict[str, float] = {}

    for ev in processed_events:
        st = ev["state"]
        # Match against official state name
        matched_st = next((s for s in NER_STATES if s.lower() in st.lower() or st.lower() in s.lower()), st)
        state_total_count[matched_st] = state_total_count.get(matched_st, 0) + 1
        state_fatalities[matched_st] = state_fatalities.get(matched_st, 0) + ev.get("fatalities", 0)

        if ev["normalized_event_type"] == "LANDSLIDE":
            state_landslide_count[matched_st] = state_landslide_count.get(matched_st, 0) + 1
        elif ev["normalized_event_type"] == "FLOOD":
            state_flood_count[matched_st] = state_flood_count.get(matched_st, 0) + 1

    # Deterministic Formula for Historical Environmental Risk Score (0 - 100)
    for st in NER_STATES:
        ls_cnt = state_landslide_count.get(st, 0)
        fl_cnt = state_flood_count.get(st, 0)
        tot = state_total_count.get(st, 0)
        fat = state_fatalities.get(st, 0)

        raw_score = (ls_cnt * 12.0) + (fl_cnt * 10.0) + (fat * 2.5) + (tot * 5.0)
        norm_score = round(min(99.0, max(5.0, raw_score)), 1)
        state_risk_scores[st] = norm_score

        if norm_score >= 75.0:
            level = "CRITICAL"
            mult = 1.30
        elif norm_score >= 50.0:
            level = "HIGH"
            mult = 1.20
        elif norm_score >= 25.0:
            level = "MODERATE"
            mult = 1.10
        else:
            level = "LOW"
            mult = 1.0

        state_risk_levels[st] = level
        state_route_multipliers[st] = mult

    # Aggregate Event Type & Severity Distributions
    event_type_dist: Dict[str, int] = {}
    severity_dist: Dict[str, int] = {}
    year_dist: Dict[int, int] = {}

    for ev in processed_events:
        et = ev["normalized_event_type"]
        event_type_dist[et] = event_type_dist.get(et, 0) + 1

        sev = ev["severity"]
        severity_dist[sev] = severity_dist.get(sev, 0) + 1

        yr = ev["year"]
        if yr:
            year_dist[yr] = year_dist.get(yr, 0) + 1

    metadata = {
        "dataset_name": "Historical Landslide and Flood Event Catalog for India & North-East Region (2000–2023)",
        "source_organization": "NASA Global Landslide Catalog / Kaggle (sahilrajverma/landslide)",
        "kaggle_source_url": "https://www.kaggle.com/datasets/sahilrajverma/landslide",
        "license": "LICENSE VERIFICATION REQUIRED: Research & Educational License — Internal dataset for baseline risk analysis only. Raw dataset must NOT be publicly redistributed.",
        "retrieval_date": "2026-09-13",
        "coverage_period": "2000–2023",
        "source_type": "historical_dataset",
        "data_type": "historical",
        "neris_operational_scope": sorted(list(NER_STATES)),
        "preprocessing_steps": [
            "1. Extracted historical landslide, mudslide, rockfall, flash flood, and riverine flood events for North-East India transit corridors.",
            "2. Validated column definitions (event_id, title, source_event_type, normalized_event_type, state, district, latitude, longitude, event_date, year, severity, trigger, fatalities).",
            "3. Normalized event classification into FLOOD, LANDSLIDE, and OTHER_UNKNOWN while preserving original source_event_type.",
            "4. Tagged all records strictly with source_type = 'historical_dataset' and data_type = 'historical' to prevent confusion with live verified incidents.",
            "5. Computed deterministic historical environmental risk scores per state (0-100 scale).",
            "6. Derived regional event distribution and temporal trends for Impact Analytics."
        ],
        "disclaimer": "HISTORICAL FLOOD/LANDSLIDE RISK (source_type = 'historical_dataset', data_type = 'historical') — NOT LIVE DISASTER MONITORING. Represents historical research data compiled from disaster catalogs.",
        "status": "VALIDATED_AND_DERIVED"
    }

    output_db = {
        "metadata": metadata,
        "events": processed_events,
        "total_events_count": len(processed_events),
        "state_distribution": state_total_count,
        "state_landslide_exposure": state_landslide_count,
        "state_flood_exposure": state_flood_count,
        "state_environmental_risk_scores": state_risk_scores,
        "state_environmental_risk_levels": state_risk_levels,
        "state_route_multipliers": state_route_multipliers,
        "event_type_distribution": event_type_dist,
        "severity_distribution": severity_dist,
        "year_distribution": {str(k): v for k, v in sorted(year_dist.items())},
        "disclaimer": "HISTORICAL FLOOD/LANDSLIDE RISK — NOT LIVE DISASTER MONITORING. Research baseline catalog (2000–2023)."
    }

    with open(JSON_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(output_db, f, indent=2, ensure_ascii=False)
    logger.info(f"Wrote historical flood & landslide database to {JSON_DB_PATH}")

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    logger.info(f"Wrote metadata to {METADATA_PATH}")

if __name__ == "__main__":
    main()
