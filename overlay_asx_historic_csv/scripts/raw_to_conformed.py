#!/usr/bin/env python3
"""Convert raw ASX tabular objects into conformed parquet objects in MinIO."""

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

from asx_overlay_common import (
    CONFORMED_BUCKET,
    RAW_BUCKET,
    detect_tabular_source_type,
    load_config,
    load_dotenv,
    normalise_jobs,
    s3_client,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transform raw ASX tabular objects into conformed parquet objects."
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


def ensure_dependencies() -> None:
    if not importlib.util.find_spec("pyarrow") and not importlib.util.find_spec("fastparquet"):
        raise RuntimeError(
            "Parquet support is unavailable. Install 'pyarrow' or 'fastparquet' before running raw_to_conformed.py."
        )


def standardise_column_name(column_name: Any) -> str:
    name = str(column_name).strip().lower()
    name = re.sub(r"[^0-9a-zA-Z]+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_")


def normalise_frame_types(frame: pd.DataFrame) -> pd.DataFrame:
    normalised = frame.convert_dtypes()
    object_columns = normalised.select_dtypes(include=["object"]).columns.tolist()
    for column in object_columns:
        normalised[column] = normalised[column].astype("string")
    return normalised


def discover_tabular_keys(s3, raw_prefix: str) -> list[str]:
    continuation_token = None
    keys: list[str] = []

    while True:
        kwargs: dict[str, Any] = {"Bucket": RAW_BUCKET, "Prefix": raw_prefix}
        if continuation_token:
            kwargs["ContinuationToken"] = continuation_token

        response = s3.list_objects_v2(**kwargs)
        for obj in response.get("Contents", []):
            object_key = obj["Key"]
            if detect_tabular_source_type(object_key, None):
                keys.append(object_key)

        if not response.get("IsTruncated"):
            break
        continuation_token = response.get("NextContinuationToken")

    if not keys:
        raise FileNotFoundError(
            f"No supported tabular objects found in raw bucket '{RAW_BUCKET}' with prefix '{raw_prefix}'."
        )

    return sorted(keys)


def read_excel_frame(
    payload: bytes, object_key: str, source_options: dict[str, Any], engine: str, source_type: str
) -> tuple[pd.DataFrame, str]:
    if importlib.util.find_spec(engine) is None:
        raise RuntimeError(
            f"Excel support is unavailable. Install '{engine}' before processing .{source_type} raw objects."
        )

    workbook = pd.ExcelFile(io.BytesIO(payload), engine=engine)
    configured_sheet_name = source_options.get("sheet_name")

    if configured_sheet_name:
        if configured_sheet_name not in workbook.sheet_names:
            available = ", ".join(workbook.sheet_names)
            raise ValueError(
                f"Configured sheet_name '{configured_sheet_name}' not found in '{object_key}'. "
                f"Available sheets: {available}"
            )
        sheet_name = str(configured_sheet_name)
    elif len(workbook.sheet_names) == 1:
        sheet_name = workbook.sheet_names[0]
    else:
        available = ", ".join(workbook.sheet_names)
        raise ValueError(
            f"Workbook '{object_key}' contains multiple sheets. Set source_options.sheet_name. "
            f"Available sheets: {available}"
        )

    header_row = int(source_options.get("header_row", 0))
    skip_rows = source_options.get("skip_rows", 0)
    frame = pd.read_excel(
        workbook,
        sheet_name=sheet_name,
        header=header_row,
        skiprows=skip_rows,
        engine=engine,
    )
    return frame, sheet_name


def read_csv_frame(payload: bytes, source_options: dict[str, Any]) -> pd.DataFrame:
    header_row = int(source_options.get("header_row", 0))
    skip_rows = source_options.get("skip_rows", 0)
    return pd.read_csv(
        io.BytesIO(payload),
        header=header_row,
        skiprows=skip_rows,
    )


def read_tabular_frame(payload: bytes, object_key: str, source_options: dict[str, Any]) -> tuple[pd.DataFrame, str | None, str]:
    source_type = detect_tabular_source_type(object_key, None)
    if source_type == "csv":
        return read_csv_frame(payload, source_options), None, source_type
    if source_type == "xls":
        frame, sheet_name = read_excel_frame(payload, object_key, source_options, "xlrd", source_type)
        return frame, sheet_name, source_type
    if source_type == "xlsx":
        frame, sheet_name = read_excel_frame(payload, object_key, source_options, "openpyxl", source_type)
        return frame, sheet_name, source_type
    raise ValueError(f"Unsupported raw object type for conformed transform: {object_key}")


def transform_job(s3, job: dict[str, Any]) -> dict[str, Any]:
    raw_keys = discover_tabular_keys(s3, job["raw_target"])

    frames: list[pd.DataFrame] = []
    source_objects: list[dict[str, Any]] = []

    for object_key in raw_keys:
        response = s3.get_object(Bucket=RAW_BUCKET, Key=object_key)
        payload = response["Body"].read()
        frame, sheet_name, source_type = read_tabular_frame(payload, object_key, job["source_options"])
        frame.columns = [standardise_column_name(column) for column in frame.columns]
        frame = normalise_frame_types(frame)
        frame["source_object_key"] = object_key
        frame["source_file_type"] = source_type
        if sheet_name is not None:
            frame["source_sheet_name"] = sheet_name
        frames.append(frame)
        source_objects.append(
            {
                "object_key": object_key,
                "source_type": source_type,
                "sheet_name": sheet_name,
                "row_count": int(len(frame)),
            }
        )

    combined = pd.concat(frames, ignore_index=True)
    combined = normalise_frame_types(combined)
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
        "raw_bucket": RAW_BUCKET,
        "raw_prefix": job["raw_target"],
        "conformed_bucket": CONFORMED_BUCKET,
        "conformed_key": job["conformed_target"],
        "raw_file_count": len(raw_keys),
        "row_count": int(len(combined)),
        "columns": combined.columns.tolist(),
        "source_objects": source_objects,
    }


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(repo_root)
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = repo_root / config_path

    try:
        ensure_dependencies()
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
