import sys
import os
import csv
import json
import logging
from typing import List, Dict, Any

# Setup structured logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("neris.ingest_rainfall")

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV_PATH = os.path.join(BASE_DIR, "backend", "app", "data", "historical_rainfall_india_1901_2017.csv")
METADATA_PATH = os.path.join(BASE_DIR, "backend", "app", "data", "historical_rainfall_metadata.json")
OUTPUT_JSON_PATH = os.path.join(BASE_DIR, "backend", "app", "data", "historical_rainfall_db.json")

REQUIRED_COLUMNS = [
    "SUBDIVISION", "YEAR", "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
    "JUL", "AUG", "SEP", "OCT", "NOV", "DEC", "ANNUAL",
    "Jan-Feb", "Mar-May", "Jun-Sep", "Oct-Dec"
]

NER_SUBDIVISIONS = {
    "ASSAM & MEGHALAYA": {
        "region_code": "NER_AM",
        "states": ["Assam", "Meghalaya"],
        "primary_hubs": ["Guwahati", "Shillong", "Silchar", "Tezpur", "Jowai"]
    },
    "ARUNACHAL PRADESH": {
        "region_code": "NER_AP",
        "states": ["Arunachal Pradesh"],
        "primary_hubs": ["Itanagar", "Tawang", "Pasighat"]
    },
    "NAGA MANI MIZO TRIPURA": {
        "region_code": "NER_NMMT",
        "states": ["Nagaland", "Manipur", "Mizoram", "Tripura"],
        "primary_hubs": ["Kohima", "Imphal", "Aizawl", "Agartala"]
    },
    "SUB HIMALAYAN WEST BENGAL & SIKKIM": {
        "region_code": "NER_SK",
        "states": ["Sikkim"],
        "primary_hubs": ["Gangtok"]
    }
}

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

def ingest_and_process():
    logger.info(f"Reading raw historical rainfall dataset from: {CSV_PATH}")
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
    normalized_monthly_records: List[Dict[str, Any]] = []
    unmapped_raw_records: List[Dict[str, Any]] = []

    subdivision_monthly_totals: Dict[str, Dict[str, List[float]]] = {sub: {m: [] for m in MONTHS} for sub in NER_SUBDIVISIONS}
    subdivision_annual_records: Dict[str, List[Dict[str, Any]]] = {sub: [] for sub in NER_SUBDIVISIONS}

    for row in raw_rows:
        sub = str(row.get("SUBDIVISION") or "").strip().upper()
        
        try:
            year = int(row.get("YEAR") or 0)
        except ValueError:
            year = None

        if sub not in NER_SUBDIVISIONS:
            # Preserve unmapped region records for dataset completeness
            unmapped_raw_records.append({
                "record_id": f"RAW-{len(unmapped_raw_records)+1:06d}",
                "source": "IMD/data.gov.in",
                "dataset": "Sub Divisional Monthly Rainfall 1901-2017",
                "region": sub,
                "year": year,
                "raw_data": row,
                "data_type": "historical",
                "source_type": "historical_dataset",
                "is_ner_operational": False
            })
            continue

        if year is None or year < 1901 or year > 2017:
            continue

        monthly_vals = {}
        for m in MONTHS:
            val_str = (row.get(m) or "").strip()
            if val_str == "" or val_str.upper() in ["NA", "N/A", "NULL"]:
                val = None
            else:
                try:
                    val = float(val_str)
                    if val < 0: val = None
                except ValueError:
                    val = None

            monthly_vals[m] = round(val, 1) if val is not None else None
            if val is not None:
                subdivision_monthly_totals[sub][m].append(val)

            # Generate normalized record conforming to Step 3 schema
            rec_id = f"RF-{sub.replace(' ', '_').replace('&', 'AND')}-{year}-{m}"
            normalized_monthly_records.append({
                "record_id": rec_id,
                "source": "IMD/data.gov.in",
                "dataset": "Sub Divisional Monthly Rainfall 1901-2017",
                "region": sub,
                "year": year,
                "month": m,
                "rainfall_mm": round(val, 1) if val is not None else None,
                "data_type": "historical",
                "source_type": "historical_dataset"
            })

        # Calculate annual total from valid non-null monthly values or source ANNUAL column
        valid_months = [v for v in monthly_vals.values() if v is not None]
        try:
            annual_val_str = (row.get("ANNUAL") or "").strip()
            annual = float(annual_val_str) if annual_val_str and annual_val_str.upper() not in ["NA", "N/A"] else sum(valid_months)
        except ValueError:
            annual = sum(valid_months) if valid_months else None

        try:
            jun_sep_str = (row.get("Jun-Sep") or "").strip()
            jun_sep = float(jun_sep_str) if jun_sep_str and jun_sep_str.upper() not in ["NA", "N/A"] else sum([monthly_vals[m] for m in ["JUN", "JUL", "AUG", "SEP"] if monthly_vals[m] is not None])
        except ValueError:
            jun_sep = sum([monthly_vals[m] for m in ["JUN", "JUL", "AUG", "SEP"] if monthly_vals[m] is not None])

        rec = {
            "subdivision": sub,
            "year": year,
            "annual_mm": round(annual, 1) if annual is not None else None,
            "monsoon_mm": round(jun_sep, 1) if jun_sep is not None else None,
            "monthly_mm": monthly_vals
        }
        cleaned_records.append(rec)
        subdivision_annual_records[sub].append(rec)

    logger.info(f"Processed {len(cleaned_records)} scoped North-East rainfall records across {len(NER_SUBDIVISIONS)} subdivisions ({len(unmapped_raw_records)} unmapped records preserved).")

    # Calculate 117-year monthly baselines and risk indices
    baselines: Dict[str, Dict[str, Any]] = {}
    for sub, month_dict in subdivision_monthly_totals.items():
        monthly_means = {}
        for m, vals in month_dict.items():
            monthly_means[m] = round(sum(vals) / len(vals), 1) if vals else None

        valid_means = [v for v in monthly_means.values() if v is not None]
        max_mean_m = max(valid_means) if valid_means else 1.0

        # Normalized monthly risk index (0.0 to 1.0)
        monthly_risk_indices = {}
        for m, mean_val in monthly_means.items():
            if mean_val is None:
                risk_score = 0.0
            else:
                risk_score = round(min(1.0, mean_val / max(500.0, max_mean_m)), 3)
            monthly_risk_indices[m] = risk_score

        annual_vals = [r["annual_mm"] for r in subdivision_annual_records[sub] if r["annual_mm"] is not None]
        avg_annual = round(sum(annual_vals) / len(annual_vals), 1) if annual_vals else None

        monsoon_vals = [r["monsoon_mm"] for r in subdivision_annual_records[sub] if r["monsoon_mm"] is not None]
        avg_monsoon = round(sum(monsoon_vals) / len(monsoon_vals), 1) if monsoon_vals else None

        baselines[sub] = {
            "subdivision": sub,
            "region_code": NER_SUBDIVISIONS[sub]["region_code"],
            "states": NER_SUBDIVISIONS[sub]["states"],
            "primary_hubs": NER_SUBDIVISIONS[sub]["primary_hubs"],
            "coverage_years": "1901-2017",
            "average_annual_mm": avg_annual,
            "average_monsoon_mm": avg_monsoon,
            "monthly_means_mm": monthly_means,
            "monthly_risk_indices": monthly_risk_indices
        }

    # Annual rainfall trends (1901-2017) aggregate across NER
    yearly_aggregates: Dict[int, float] = {}
    yearly_counts: Dict[int, int] = {}
    for r in cleaned_records:
        y = r["year"]
        if r["annual_mm"] is not None:
            yearly_aggregates[y] = yearly_aggregates.get(y, 0.0) + r["annual_mm"]
            yearly_counts[y] = yearly_counts.get(y, 0) + 1

    trend_series = []
    for y in sorted(yearly_aggregates.keys()):
        avg = round(yearly_aggregates[y] / max(1, yearly_counts[y]), 1)
        trend_series.append({"year": y, "avg_annual_mm": avg})

    # Historical Extreme wettest years
    valid_cleaned = [r for r in cleaned_records if r["annual_mm"] is not None]
    sorted_extreme_records = sorted(valid_cleaned, key=lambda x: x["annual_mm"], reverse=True)[:10]
    extreme_years = [
        {
            "rank": idx + 1,
            "subdivision": r["subdivision"],
            "year": r["year"],
            "annual_rainfall_mm": r["annual_mm"],
            "monsoon_rainfall_mm": r["monsoon_mm"],
            "disclaimer": "Historical High-Rainfall Record (1901-2017 IMD Baseline)"
        }
        for idx, r in enumerate(sorted_extreme_records)
    ]

    # Load metadata
    metadata = {}
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, "r", encoding="utf-8") as mf:
            metadata = json.load(mf)

    output_db = {
        "metadata": metadata,
        "baselines": baselines,
        "annual_trend_series": trend_series,
        "extreme_rainfall_records": extreme_years,
        "normalized_records_sample": normalized_monthly_records[:50],
        "processed_records_count": len(cleaned_records),
        "unmapped_records_count": len(unmapped_raw_records),
        "disclaimer": "HISTORICAL RAINFALL — NOT LIVE WEATHER. Multi-decade statistical baseline (1901–2017)."
    }

    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as out_f:
        json.dump(output_db, out_f, indent=2)

    logger.info(f"Successfully generated historical rainfall database cache: {OUTPUT_JSON_PATH}")

    # Attempt AWS DynamoDB and S3 persistence if configured
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
            s3.upload_file(CSV_PATH, bucket_name, "historical/rainfall/raw/historical_rainfall_india_1901_2017.csv")
            s3.upload_file(OUTPUT_JSON_PATH, bucket_name, "historical/rainfall/processed/historical_rainfall_db.json")
            if os.path.exists(METADATA_PATH):
                s3.upload_file(METADATA_PATH, bucket_name, "historical/rainfall/metadata/historical_rainfall_metadata.json")
            logger.info(f"Uploaded raw, processed, and metadata rainfall objects to s3://{bucket_name}/historical/rainfall/")
        except Exception as s3_err:
            logger.warning(f"S3 upload notice (local/simulated env): {s3_err}")

        table_name = os.environ.get("HISTORICAL_RAINFALL_TABLE", "ner_historical_rainfall")
        dynamodb = boto3.resource("dynamodb", region_name=region)
        table = dynamodb.Table(table_name)
        
        for sub, bdata in baselines.items():
            dynamo_item = convert_floats(bdata)
            table.put_item(Item=dynamo_item)
        logger.info(f"Persisted {len(baselines)} historical rainfall baseline records to AWS DynamoDB ('{table_name}').")
    except Exception as e:
        logger.warning(f"AWS persistence notice: {e}. Local fallback cache active at '{OUTPUT_JSON_PATH}'.")

if __name__ == "__main__":
    ingest_and_process()

