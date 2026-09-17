import sys
import os
import csv
import json
import logging
from typing import List, Dict, Any, Optional

# Setup structured logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("neris.ingest_road_accidents")

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV_PATH = os.path.join(BASE_DIR, "backend", "app", "data", "historical_road_accident_dataset_2022_2025.csv")
METADATA_PATH = os.path.join(BASE_DIR, "backend", "app", "data", "historical_road_accident_metadata.json")
OUTPUT_JSON_PATH = os.path.join(BASE_DIR, "backend", "app", "data", "historical_road_accidents_db.json")

REQUIRED_COLUMNS = [
    "accident_id", "date_time", "year", "time_of_day", "state", "district",
    "road_type", "severity", "weather_condition", "visibility", "traffic_density",
    "speed_limit_kmh", "vehicles_involved", "casualties_count", "latitude", "longitude", "is_synthetic"
]

NER_STATES = ["Assam", "Meghalaya", "Arunachal Pradesh", "Nagaland", "Manipur", "Mizoram", "Tripura", "Sikkim"]

# Historical Road Risk Score Weights (Deterministic Formula)
SEVERITY_WEIGHTS = {
    "Fatal": 4.0,
    "Severe Injury": 2.5,
    "Minor Injury": 1.0,
    "Property Damage Only": 0.5
}

TRAFFIC_WEIGHTS = {
    "Congested": 1.5,
    "High": 1.3,
    "Medium": 1.0,
    "Low": 0.7
}

WEATHER_WEIGHTS = {
    "Heavy Rain": 1.5,
    "Rain": 1.3,
    "Fog/Mist": 1.4,
    "Clear": 1.0
}

VISIBILITY_WEIGHTS = {
    "Poor": 1.5,
    "Reduced": 1.2,
    "Normal": 1.0
}

def ingest_and_process():
    logger.info(f"Reading raw historical road accident dataset from: {CSV_PATH}")
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Missing input dataset CSV at: {CSV_PATH}")

    raw_rows: List[Dict[str, str]] = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        
        # Validate columns
        for col in REQUIRED_COLUMNS:
            if col not in fieldnames:
                raise ValueError(f"Dataset Validation Error: Missing required column '{col}'")

        for r in reader:
            raw_rows.append(r)

    logger.info(f"Successfully loaded {len(raw_rows)} raw records. Validating and transforming dataset...")

    cleaned_records: List[Dict[str, Any]] = []
    normalized_records: List[Dict[str, Any]] = []
    unmapped_raw_records: List[Dict[str, Any]] = []

    state_stats: Dict[str, Dict[str, Any]] = {
        st: {
            "state": st,
            "total_accidents": 0,
            "fatal_accidents": 0,
            "severe_injuries": 0,
            "minor_injuries": 0,
            "total_casualties": 0,
            "vehicles_involved_total": 0,
            "severity_breakdown": {},
            "road_type_breakdown": {},
            "weather_breakdown": {},
            "visibility_breakdown": {},
            "time_of_day_breakdown": {},
            "traffic_density_breakdown": {},
            "risk_scores": []
        }
        for st in NER_STATES
    }

    yearly_counts: Dict[int, int] = {}
    severity_counts: Dict[str, int] = {}
    weather_counts: Dict[str, int] = {}
    road_type_counts: Dict[str, int] = {}
    time_of_day_counts: Dict[str, int] = {}

    for row in raw_rows:
        st_raw = (row.get("state") or "").strip()
        
        # Match state to NER scope
        matched_state = None
        for ner_s in NER_STATES:
            if ner_s.lower() == st_raw.lower() or ner_s.lower() in st_raw.lower() or st_raw.lower() in ner_s.lower():
                matched_state = ner_s
                break

        if not matched_state:
            # Preserve unmapped national record
            unmapped_raw_records.append({
                "accident_id": row.get("accident_id"),
                "source": "Kaggle (sehaj1104/indian-road-accident-dataset-20222025)",
                "raw_data": row,
                "data_type": "historical",
                "source_type": "historical_synthetic_dataset",
                "is_ner_operational": False
            })
            continue

        try:
            year = int(row.get("year") or 0)
        except ValueError:
            year = None

        if year is None or year < 2020 or year > 2026:
            continue

        severity = (row.get("severity") or "Minor Injury").strip()
        road_type = (row.get("road_type") or "National Highway").strip()
        weather = (row.get("weather_condition") or "Clear").strip()
        visibility = (row.get("visibility") or "Normal").strip()
        traffic = (row.get("traffic_density") or "Medium").strip()
        tod = (row.get("time_of_day") or "Afternoon").strip()

        try:
            casualties = int(row.get("casualties_count") or 0)
        except ValueError:
            casualties = 0

        try:
            vehicles = int(row.get("vehicles_involved") or 1)
        except ValueError:
            vehicles = 1

        is_synth = str(row.get("is_synthetic") or "True").strip().lower() == "true"

        # Calculate deterministic historical road-risk score for this event
        sev_w = SEVERITY_WEIGHTS.get(severity, 1.0)
        trf_w = TRAFFIC_WEIGHTS.get(traffic, 1.0)
        wth_w = WEATHER_WEIGHTS.get(weather, 1.0)
        vis_w = VISIBILITY_WEIGHTS.get(visibility, 1.0)

        # Formula: historical_road_risk = (severity_weight * 1.5) + (weather_weight * 1.2) + (visibility_weight * 1.1) + (traffic_weight * 1.0)
        event_risk_score = round((sev_w * 1.5) + (wth_w * 1.2) + (vis_w * 1.1) + (trf_w * 1.0), 2)

        rec = {
            "accident_id": row.get("accident_id"),
            "source": "Kaggle (sehaj1104/indian-road-accident-dataset-20222025)",
            "dataset": "Indian Road Accident Dataset 2022-2025",
            "state": matched_state,
            "district": row.get("district") or "Unknown District",
            "year": year,
            "date_time": row.get("date_time"),
            "time_of_day": tod,
            "road_type": road_type,
            "severity": severity,
            "weather_condition": weather,
            "visibility": visibility,
            "traffic_density": traffic,
            "speed_limit_kmh": int(row.get("speed_limit_kmh") or 50),
            "vehicles_involved": vehicles,
            "casualties_count": casualties,
            "event_risk_score": event_risk_score,
            "is_synthetic_coordinates": is_synth,
            "data_type": "historical",
            "source_type": "historical_synthetic_dataset"
        }
        cleaned_records.append(rec)
        normalized_records.append(rec)

        # Update state aggregations
        st_obj = state_stats[matched_state]
        st_obj["total_accidents"] += 1
        st_obj["total_casualties"] += casualties
        st_obj["vehicles_involved_total"] += vehicles
        st_obj["risk_scores"].append(event_risk_score)

        if severity == "Fatal": st_obj["fatal_accidents"] += 1
        elif severity == "Severe Injury": st_obj["severe_injuries"] += 1
        elif severity == "Minor Injury": st_obj["minor_injuries"] += 1

        st_obj["severity_breakdown"][severity] = st_obj["severity_breakdown"].get(severity, 0) + 1
        st_obj["road_type_breakdown"][road_type] = st_obj["road_type_breakdown"].get(road_type, 0) + 1
        st_obj["weather_breakdown"][weather] = st_obj["weather_breakdown"].get(weather, 0) + 1
        st_obj["visibility_breakdown"][visibility] = st_obj["visibility_breakdown"].get(visibility, 0) + 1
        st_obj["time_of_day_breakdown"][tod] = st_obj["time_of_day_breakdown"].get(tod, 0) + 1
        st_obj["traffic_density_breakdown"][traffic] = st_obj["traffic_density_breakdown"].get(traffic, 0) + 1

        # Global aggregations
        yearly_counts[year] = yearly_counts.get(year, 0) + 1
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        weather_counts[weather] = weather_counts.get(weather, 0) + 1
        road_type_counts[road_type] = road_type_counts.get(road_type, 0) + 1
        time_of_day_counts[tod] = time_of_day_counts.get(tod, 0) + 1

    logger.info(f"Processed {len(cleaned_records)} scoped North-East road accident records across {len(NER_STATES)} states ({len(unmapped_raw_records)} unmapped records preserved).")

    # Compute final state risk indices
    state_baselines: Dict[str, Dict[str, Any]] = {}
    for st, data in state_stats.items():
        cnt = data["total_accidents"]
        r_scores = data["risk_scores"]
        avg_risk = round(sum(r_scores) / len(r_scores), 2) if r_scores else 1.0

        if avg_risk >= 7.5:
            r_level = "CRITICAL"
        elif avg_risk >= 5.5:
            r_level = "HIGH"
        elif avg_risk >= 3.5:
            r_level = "MODERATE"
        else:
            r_level = "LOW"

        # Normalized risk factor multiplier for route planner (1.0x to 1.35x)
        route_risk_weight = round(1.0 + (min(1.0, avg_risk / 10.0) * 0.35), 3)

        state_baselines[st] = {
            "state": st,
            "total_accidents": cnt,
            "fatal_accidents": data["fatal_accidents"],
            "severe_injuries": data["severe_injuries"],
            "total_casualties": data["total_casualties"],
            "average_event_risk_score": avg_risk,
            "risk_level": r_level,
            "route_risk_multiplier": route_risk_weight,
            "severity_breakdown": data["severity_breakdown"],
            "road_type_breakdown": data["road_type_breakdown"],
            "weather_breakdown": data["weather_breakdown"],
            "time_of_day_breakdown": data["time_of_day_breakdown"],
            "disclaimer": "HISTORICAL ROAD RISK — NOT LIVE ACCIDENT DATA"
        }

    yearly_trend_series = [{"year": y, "accident_count": cnt} for y, cnt in sorted(yearly_counts.items())]

    # Load metadata
    metadata = {}
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, "r", encoding="utf-8") as mf:
            metadata = json.load(mf)

    output_db = {
        "metadata": metadata,
        "state_baselines": state_baselines,
        "annual_trend_series": yearly_trend_series,
        "severity_distribution": severity_counts,
        "weather_distribution": weather_counts,
        "road_type_distribution": road_type_counts,
        "time_of_day_distribution": time_of_day_counts,
        "processed_records_count": len(cleaned_records),
        "unmapped_records_count": len(unmapped_raw_records),
        "disclaimer": "HISTORICAL ROAD RISK — NOT LIVE ACCIDENT DATA. Multi-year statistical baseline (2022–2025)."
    }

    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as out_f:
        json.dump(output_db, out_f, indent=2)

    logger.info(f"Successfully generated historical road accident database cache: {OUTPUT_JSON_PATH}")

    # Attempt AWS DynamoDB & S3 persistence if configured
    try:
        import boto3
        from decimal import Decimal

        def convert_floats(obj):
            if isinstance(obj, float):
                return Decimal(str(obj))
            elif isinstance(obj, dict):
                return {k: convert_floats(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_floats(i) for i in obj]
            return obj

        region = os.environ.get("AWS_REGION", "ap-south-1")
        bucket_name = os.environ.get("S3_BUCKET_EVIDENCE", "neris-evidence-photos-ap-south-1")

        # Upload files to S3 paths
        s3 = boto3.client("s3", region_name=region)
        try:
            s3.upload_file(CSV_PATH, bucket_name, "historical/road-accidents/raw/historical_road_accident_dataset_2022_2025.csv")
            s3.upload_file(OUTPUT_JSON_PATH, bucket_name, "historical/road-accidents/processed/historical_road_accidents_db.json")
            if os.path.exists(METADATA_PATH):
                s3.upload_file(METADATA_PATH, bucket_name, "historical/road-accidents/metadata/historical_road_accident_metadata.json")
            logger.info(f"Uploaded raw, processed, and metadata road accident objects to s3://{bucket_name}/historical/road-accidents/")
        except Exception as s3_err:
            logger.warning(f"S3 upload notice (local/simulated env): {s3_err}")

        table_name = os.environ.get("HISTORICAL_ROAD_ACCIDENTS_TABLE", "ner_historical_road_accidents")
        dynamodb = boto3.resource("dynamodb", region_name=region)
        table = dynamodb.Table(table_name)
        
        for st, bdata in state_baselines.items():
            dynamo_item = convert_floats(bdata)
            table.put_item(Item=dynamo_item)
        logger.info(f"Persisted {len(state_baselines)} historical road risk baseline records to AWS DynamoDB ('{table_name}').")
    except Exception as e:
        logger.warning(f"AWS persistence notice: {e}. Local fallback cache active at '{OUTPUT_JSON_PATH}'.")

if __name__ == "__main__":
    ingest_and_process()
