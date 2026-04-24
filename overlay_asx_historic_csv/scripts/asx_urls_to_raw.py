#!/usr/bin/env python3
"""Download ASX historic tabular URLs and land them in the raw MinIO bucket."""

from __future__ import annotations

import argparse
import json
import mimetypes
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

from asx_overlay_common import (
    RAW_BUCKET,
    delete_prefix,
    detect_tabular_source_type,
    load_config,
    load_dotenv,
    normalise_jobs,
    s3_client,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download ASX historic tabular URLs defined in JSON config into raw MinIO storage."
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
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete existing raw objects under the configured prefix before uploading new files.",
    )
    return parser.parse_args()


def object_name_for_url(url: str, index: int, used_names: set[str]) -> str:
    parsed_url = urlparse(url)
    path_name = unquote(Path(parsed_url.path).name)
    file_name = path_name or f"source_{index}.csv"
    if not Path(file_name).suffix:
        file_name = f"{file_name}.csv"

    candidate = file_name
    suffix = Path(file_name).suffix
    stem = Path(file_name).stem
    counter = 2
    while candidate in used_names:
        candidate = f"{stem}_{counter}{suffix}"
        counter += 1

    used_names.add(candidate)
    return candidate


def download_url(url: str) -> tuple[bytes, str | None, str]:
    request = Request(url, headers={"User-Agent": "oss-data-lake-asx-historic-csv/1.0"})
    with urlopen(request, timeout=60) as response:
        content_type = response.headers.get("Content-Type")
        content = response.read()

    if not content:
        raise ValueError(f"Downloaded empty content from {url}")

    source_type = detect_tabular_source_type(url, content_type)
    if not source_type:
        raise ValueError(
            "Source URL is not a supported tabular file. "
            f"Expected .csv, .xls, or .xlsx: {url} (content-type: {content_type or 'unknown'})"
        )

    return content, content_type, source_type


def prepare_downloads(job: dict[str, Any]) -> list[dict[str, Any]]:
    downloaded_objects: list[dict[str, Any]] = []
    used_names: set[str] = set()

    for index, source_url in enumerate(job["source_urls"], start=1):
        file_name = object_name_for_url(source_url, index, used_names)
        content, response_content_type, source_type = download_url(source_url)
        content_type = response_content_type or mimetypes.guess_type(file_name)[0] or "text/csv"
        downloaded_objects.append(
            {
                "source_url": source_url,
                "file_name": file_name,
                "content": content,
                "content_type": content_type,
                "source_type": source_type,
            }
        )

    return downloaded_objects


def ingest_job(job: dict[str, Any], replace: bool) -> dict[str, Any]:
    downloaded_objects = prepare_downloads(job)
    if not downloaded_objects:
        raise RuntimeError(f"Job '{job['name']}' produced no raw objects.")

    s3 = s3_client()
    raw_prefix = job["raw_target"]
    deleted_count = 0
    if replace:
        deleted_count = delete_prefix(s3, RAW_BUCKET, raw_prefix)

    uploaded_objects: list[dict[str, Any]] = []
    for downloaded_object in downloaded_objects:
        file_name = downloaded_object["file_name"]
        object_key = f"{raw_prefix}/{file_name}"
        s3.put_object(
            Bucket=RAW_BUCKET,
            Key=object_key,
            Body=downloaded_object["content"],
            ContentType=downloaded_object["content_type"],
        )
        uploaded_objects.append(
            {
                "source_url": downloaded_object["source_url"],
                "object_key": object_key,
                "bytes": len(downloaded_object["content"]),
                "source_type": downloaded_object["source_type"],
            }
        )

    return {
        "job_name": job["name"],
        "raw_bucket": RAW_BUCKET,
        "raw_prefix": raw_prefix,
        "deleted_object_count": deleted_count,
        "file_count": len(uploaded_objects),
        "objects": uploaded_objects,
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
        results = [ingest_job(job, args.replace) for job in jobs]
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"ingested_jobs": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
