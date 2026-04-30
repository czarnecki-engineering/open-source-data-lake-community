#!/usr/bin/env python3
"""Download Kaggle datasets and land extracted files in the raw MinIO bucket."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from kaggle_overlay_common import RAW_BUCKET, delete_prefix, load_config, load_dotenv, normalise_jobs, s3_client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download Kaggle datasets defined in a JSON config into raw MinIO storage."
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
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete existing raw objects under the configured prefix before uploading new files.",
    )
    return parser.parse_args()


def validate_kaggle_auth() -> str:
    if os.getenv("KAGGLE_API_TOKEN"):
        return "access_token"
    if os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY"):
        return "legacy_api_key"
    raise EnvironmentError(
        "Missing Kaggle credentials. Set KAGGLE_API_TOKEN, or set both KAGGLE_USERNAME and KAGGLE_KEY."
    )


def get_kaggle_api() -> tuple[Any, str]:
    auth_mode = validate_kaggle_auth()

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError as exc:
        raise ImportError(
            "The kaggle package is required. Install it with 'pip install kaggle'."
        ) from exc

    api = KaggleApi()
    api.authenticate()
    return api, auth_mode


def upload_tree_contents(s3, source_dir: Path, bucket: str, prefix: str) -> list[str]:
    uploaded_keys: list[str] = []

    for source_path in sorted(source_dir.rglob("*")):
        if not source_path.is_file():
            continue

        relative_path = source_path.relative_to(source_dir).as_posix()
        object_key = f"{prefix}/{relative_path}"
        s3.upload_file(str(source_path), bucket, object_key)
        uploaded_keys.append(object_key)

    return uploaded_keys


def ingest_job(api: Any, job: dict[str, str], replace: bool) -> dict[str, Any]:
    s3 = s3_client()
    raw_prefix = job["raw_target"]
    deleted_count = 0
    if replace:
        deleted_count = delete_prefix(s3, RAW_BUCKET, raw_prefix)

    with tempfile.TemporaryDirectory(prefix="kaggle_download_") as temp_dir_name:
        download_dir = Path(temp_dir_name) / "download"
        download_dir.mkdir(parents=True, exist_ok=True)

        print(f"Downloading dataset '{job['dataset']}' for job '{job['name']}'")
        api.dataset_download_files(
            job["dataset"],
            path=str(download_dir),
            unzip=True,
            quiet=False,
        )

        uploaded_keys = upload_tree_contents(s3, download_dir, RAW_BUCKET, raw_prefix)

    if not uploaded_keys:
        raise RuntimeError(
            f"Dataset '{job['dataset']}' downloaded successfully but no files were uploaded."
        )

    return {
        "job_name": job["name"],
        "dataset": job["dataset"],
        "raw_bucket": RAW_BUCKET,
        "raw_prefix": raw_prefix,
        "deleted_object_count": deleted_count,
        "file_count": len(uploaded_keys),
        "objects": uploaded_keys,
    }


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(repo_root)
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = repo_root / config_path

    try:
        payload = load_config(config_path)
        requested_jobs = set(args.job_names) if args.job_names else None
        jobs = normalise_jobs(payload, requested_jobs)
        api, auth_mode = get_kaggle_api()
        results = [ingest_job(api, job, args.replace) for job in jobs]
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"authentication": auth_mode, "ingested_jobs": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
