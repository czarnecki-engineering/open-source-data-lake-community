#!/usr/bin/env python3
"""Convert raw Kaggle CSV objects into conformed parquet objects in MinIO."""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from kaggle_overlay_common import (
    CONFORMED_BUCKET,
    RAW_BUCKET,
    load_config,
    load_dotenv,
    normalise_jobs,
    s3_client,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transform raw Kaggle CSV objects into conformed parquet objects."
    )
    parser.add_argument(
        "--config",
        default="config/kaggle_jobs.json",
        help="Path to the Kaggle jobs JSON file. Defaults to config/kaggle_jobs.json.",
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
        "Parquet support is unavailable. Install 'pyarrow' or 'fastparquet' before running raw_to_conformed.py."
    )


def standardise_column_name(column_name: Any) -> str:
    name = str(column_name).strip().lower()
    name = re.sub(r"[^0-9a-zA-Z]+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_")


def discover_csv_keys(s3, raw_prefix: str) -> list[str]:
    continuation_token = None
    keys: list[str] = []

    while True:
        kwargs: dict[str, Any] = {"Bucket": RAW_BUCKET, "Prefix": raw_prefix}
        if continuation_token:
            kwargs["ContinuationToken"] = continuation_token
        response = s3.list_objects_v2(**kwargs)
        keys.extend(obj["Key"] for obj in response.get("Contents", []) if obj["Key"].endswith(".csv"))
        if not response.get("IsTruncated"):
            break
        continuation_token = response.get("NextContinuationToken")

    if not keys:
        raise FileNotFoundError(
            f"No CSV objects found in raw bucket '{RAW_BUCKET}' with prefix '{raw_prefix}'."
        )
    return sorted(keys)


def transform_job(s3, job: dict[str, str]) -> dict[str, Any]:
    csv_keys = discover_csv_keys(s3, job["raw_target"])

    frames: list[pd.DataFrame] = []
    for object_key in csv_keys:
        response = s3.get_object(Bucket=RAW_BUCKET, Key=object_key)
        frame = pd.read_csv(io.BytesIO(response["Body"].read()))
        frame.columns = [standardise_column_name(column) for column in frame.columns]
        frame["source_object_key"] = object_key
        frames.append(frame)

    combined = pd.concat(frames, ignore_index=True)
    buffer = io.BytesIO()
    combined.to_parquet(buffer, index=False)
    buffer.seek(0)

    s3.put_object(
        Bucket=CONFORMED_BUCKET,
        Key=job["conformed_target"],
        Body=buffer.getvalue(),
        ContentType="application/octet-stream",
    )

    return {
        "job_name": job["name"],
        "dataset": job["dataset"],
        "raw_bucket": RAW_BUCKET,
        "raw_prefix": job["raw_target"],
        "conformed_bucket": CONFORMED_BUCKET,
        "conformed_key": job["conformed_target"],
        "raw_file_count": len(csv_keys),
        "row_count": int(len(combined)),
        "columns": combined.columns.tolist(),
    }


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
        results = [transform_job(s3, job) for job in jobs]
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"conformed_jobs": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
