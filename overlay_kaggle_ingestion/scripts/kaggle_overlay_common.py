"""Shared helpers for the Kaggle overlay pipeline."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import boto3
from botocore.client import Config


RAW_BUCKET = os.getenv("KAGGLE_RAW_BUCKET", "raw")
CONFORMED_BUCKET = os.getenv("KAGGLE_CONFORMED_BUCKET", "conformed")
CURATED_BUCKET = os.getenv("KAGGLE_CURATED_BUCKET", "curated")


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


def normalise_jobs(payload: dict[str, Any], requested_jobs: set[str] | None) -> list[dict[str, str]]:
    jobs: list[dict[str, str]] = []

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
            for field in ("dataset", "raw_target", "conformed_target", "curated_target")
            if not job.get(field)
        ]
        if missing_fields:
            missing = ", ".join(missing_fields)
            raise ValueError(f"Job '{name}' is missing required fields: {missing}")

        jobs.append(
            {
                "name": name,
                "dataset": str(job["dataset"]),
                "raw_target": normalise_object_prefix(str(job["raw_target"])),
                "conformed_target": normalise_object_key(str(job["conformed_target"])),
                "curated_target": normalise_object_key(str(job["curated_target"])),
            }
        )

    if requested_jobs and not jobs:
        requested = ", ".join(sorted(requested_jobs))
        raise ValueError(f"No enabled jobs matched --job filters: {requested}")
    if not jobs:
        raise ValueError("No enabled jobs found in config.")

    return jobs


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
    return repo_root / "data" / "curated" / object_key
