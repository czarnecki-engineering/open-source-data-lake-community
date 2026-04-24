#!/usr/bin/env python3
"""Create curated JSON summary artifacts from conformed MinIO parquet objects."""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from asx_overlay_common import (
    CONFORMED_BUCKET,
    CURATED_BUCKET,
    RAW_BUCKET,
    load_config,
    load_dotenv,
    local_curated_summary_path,
    normalise_jobs,
    s3_client,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarise conformed ASX parquet objects into curated JSON artifacts."
    )
    parser.add_argument(
        "--config",
        default="config/asx_historic_jobs.json",
        help="Path to the ASX historic jobs JSON file. Defaults to config/asx_historic_jobs.json.",
    )
    parser.add_argument(
        "--job",
        action="append",
        dest="job_names",
        help="Optional job name filter. Can be supplied multiple times.",
    )
    return parser.parse_args()


def ensure_parquet_support() -> None:
    if importlib.util.find_spec("pyarrow") or importlib.util.find_spec("fastparquet"):
        return
    raise RuntimeError(
        "Parquet support is unavailable. Install 'pyarrow' or 'fastparquet' before running conformed_to_curated.py."
    )


def json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return json_safe(value.item())
    return str(value)


def build_numeric_stats(frame: pd.DataFrame) -> dict[str, dict[str, Any]]:
    numeric_columns = frame.select_dtypes(include="number")
    stats: dict[str, dict[str, Any]] = {}

    for column in numeric_columns.columns:
        series = numeric_columns[column]
        stats[column] = {
            "count": int(series.count()),
            "mean": json_safe(series.mean()),
            "min": json_safe(series.min()),
            "max": json_safe(series.max()),
            "sum": json_safe(series.sum()),
        }

    return stats


def build_type_summary(frame: pd.DataFrame) -> dict[str, str]:
    return {column: str(dtype) for column, dtype in frame.dtypes.items()}


def summarise_job(repo_root: Path, s3, job: dict[str, Any]) -> dict[str, Any]:
    try:
        response = s3.get_object(Bucket=CONFORMED_BUCKET, Key=job["conformed_target"])
    except Exception as exc:
        raise FileNotFoundError(
            f"Conformed parquet object not found: s3://{CONFORMED_BUCKET}/{job['conformed_target']}"
        ) from exc

    frame = pd.read_parquet(io.BytesIO(response["Body"].read()))
    summary = {
        "job_name": job["name"],
        "raw_bucket": RAW_BUCKET,
        "raw_prefix": job["raw_target"],
        "conformed_bucket": CONFORMED_BUCKET,
        "conformed_target": job["conformed_target"],
        "curated_bucket": CURATED_BUCKET,
        "curated_target": job["curated_target"],
        "row_count": int(len(frame)),
        "column_count": int(len(frame.columns)),
        "columns": frame.columns.tolist(),
        "dtypes": build_type_summary(frame),
        "null_counts": {column: int(value) for column, value in frame.isna().sum().items()},
        "numeric_stats": build_numeric_stats(frame),
    }

    encoded = json.dumps(summary, indent=2).encode("utf-8")
    s3.put_object(
        Bucket=CURATED_BUCKET,
        Key=job["curated_target"],
        Body=encoded,
        ContentType="application/json",
    )

    mirror_path = local_curated_summary_path(repo_root, job["curated_target"])
    mirror_path.parent.mkdir(parents=True, exist_ok=True)
    mirror_path.write_bytes(encoded)

    return summary


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(repo_root)
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = repo_root / config_path

    try:
        ensure_parquet_support()
        payload = load_config(config_path)
        requested_jobs = set(args.job_names) if args.job_names else None
        jobs = normalise_jobs(payload, requested_jobs)
        s3 = s3_client()
        results = [summarise_job(repo_root, s3, job) for job in jobs]
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"curated_jobs": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
