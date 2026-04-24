"""Shared helpers for the ASX historic tabular overlay pipeline."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import boto3
from botocore.client import Config


RAW_BUCKET = os.getenv("ASX_RAW_BUCKET", "raw")
CONFORMED_BUCKET = os.getenv("ASX_CONFORMED_BUCKET", "conformed")
CURATED_BUCKET = os.getenv("ASX_CURATED_BUCKET", "curated")
TABULAR_CONTENT_TYPES = {
    "text/csv": "csv",
    "application/csv": "csv",
    "text/plain": "csv",
    "application/vnd.ms-excel": "xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
}


def load_dotenv(repo_root: Path) -> None:
    for env_name in (".env", ".env.local"):
        env_path = repo_root / env_name
        if not env_path.exists():
            continue

        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("'").strip('"'))


def load_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if "jobs" not in payload or not isinstance(payload["jobs"], list):
        raise ValueError("Config must contain a top-level 'jobs' list.")

    return payload


def normalise_jobs(payload: dict[str, Any], requested_jobs: set[str] | None) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []

    for index, job in enumerate(payload["jobs"], start=1):
        if not isinstance(job, dict):
            raise ValueError(f"Job entry {index} must be a JSON object.")

        name = str(job.get("name") or f"job_{index}")
        if requested_jobs and name not in requested_jobs:
            continue
        if not bool(job.get("enabled", False)):
            continue

        missing_fields = [
            field
            for field in ("source_urls", "raw_target", "conformed_target", "curated_target")
            if not job.get(field)
        ]
        if missing_fields:
            missing = ", ".join(missing_fields)
            raise ValueError(f"Job '{name}' is missing required fields: {missing}")

        source_urls = normalise_source_urls(job["source_urls"], name)

        jobs.append(
            {
                "name": name,
                "source_urls": source_urls,
                "raw_target": normalise_object_prefix(str(job["raw_target"])),
                "conformed_target": normalise_object_key(str(job["conformed_target"])),
                "curated_target": normalise_object_key(str(job["curated_target"])),
                "source_options": normalise_source_options(job.get("source_options"), name),
            }
        )

    if requested_jobs and not jobs:
        requested = ", ".join(sorted(requested_jobs))
        raise ValueError(f"No enabled jobs matched --job filters: {requested}")
    if not jobs:
        raise ValueError("No enabled jobs found in config.")

    return jobs


def normalise_source_urls(value: Any, job_name: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"Job '{job_name}' must contain a non-empty source_urls list.")

    source_urls: list[str] = []
    for url in value:
        if not isinstance(url, str) or not url.strip():
            raise ValueError(f"Job '{job_name}' contains an invalid source URL.")

        clean_url = url.strip()
        scheme = urlparse(clean_url).scheme.lower()
        if scheme not in {"http", "https"}:
            raise ValueError(
                f"Job '{job_name}' source URL must use http or https: {clean_url}"
            )
        source_urls.append(clean_url)

    return source_urls


def normalise_source_options(value: Any, job_name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"Job '{job_name}' source_options must be a JSON object when provided.")
    return dict(value)


def detect_tabular_source_type(url: str, content_type: str | None) -> str | None:
    url_path = unquote(urlparse(url).path).lower()
    if url_path.endswith(".csv"):
        return "csv"
    if url_path.endswith(".xls"):
        return "xls"
    if url_path.endswith(".xlsx"):
        return "xlsx"

    if content_type:
        mime_type = content_type.split(";", 1)[0].strip().lower()
        return TABULAR_CONTENT_TYPES.get(mime_type)

    return None


def s3_client():
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("S3_ENDPOINT_URL", "http://127.0.0.1:9000"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", os.getenv("MINIO_ROOT_USER", "minioadmin")),
        aws_secret_access_key=os.getenv(
            "AWS_SECRET_ACCESS_KEY", os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
        ),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        config=Config(signature_version="s3v4"),
    )


def normalise_object_prefix(value: str) -> str:
    return value.strip().strip("/")


def normalise_object_key(value: str) -> str:
    return value.strip().lstrip("/")


def list_keys(s3, bucket: str, prefix: str) -> list[str]:
    keys: list[str] = []
    continuation_token = None

    while True:
        kwargs: dict[str, Any] = {"Bucket": bucket, "Prefix": prefix}
        if continuation_token:
            kwargs["ContinuationToken"] = continuation_token

        response = s3.list_objects_v2(**kwargs)
        keys.extend(obj["Key"] for obj in response.get("Contents", []))

        if not response.get("IsTruncated"):
            break
        continuation_token = response.get("NextContinuationToken")

    return keys


def delete_prefix(s3, bucket: str, prefix: str) -> int:
    keys = list_keys(s3, bucket, prefix)
    if not keys:
        return 0

    deleted = 0
    for start in range(0, len(keys), 1000):
        chunk = keys[start : start + 1000]
        s3.delete_objects(
            Bucket=bucket,
            Delete={"Objects": [{"Key": key} for key in chunk], "Quiet": True},
        )
        deleted += len(chunk)

    return deleted


def local_curated_summary_path(repo_root: Path, object_key: str) -> Path:
    override = os.getenv("ASX_CURATED_LOCAL_ROOT")
    curated_root = Path(override) if override else repo_root / "data" / "curated"
    return curated_root / normalise_object_key(object_key)
