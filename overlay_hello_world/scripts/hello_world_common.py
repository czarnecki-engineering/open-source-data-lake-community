from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = {
    "job_name": "hello_world",
    "run_date": "2026-04-24",
    "raw_bucket": "raw",
    "raw_key": "hello_world/raw/records.json",
    "conformed_bucket": "conformed",
    "conformed_key": "hello_world/conformed/records.json",
    "curated_bucket": "curated",
    "curated_key": "hello_world/curated/latest/summary.json",
    "enabled_solution_tag": "hello-world",
}


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def repo_root() -> Path:
    start_points = [Path.cwd(), script_dir()]
    for start in start_points:
        for candidate in [start, *start.parents]:
            if (candidate / "docker-compose.yaml").is_file():
                return candidate
    return Path.cwd()


def overlay_root() -> Path:
    current = script_dir().parent
    if current.name == "overlay_hello_world":
        return current
    return repo_root() / "overlay_hello_world"


def config_candidates() -> list[Path]:
    root = repo_root()
    env_dir = os.getenv("HELLO_WORLD_CONFIG_DIR")
    candidates: list[Path] = []

    if env_dir:
        env_path = Path(env_dir)
        candidates.extend(
            [
                env_path / "hello_world_job.json",
                env_path / "hello_world_job.example.json",
            ]
        )

    candidates.extend(
        [
            root / "config" / "hello_world_job.json",
            root / "config" / "hello_world_job.example.json",
            overlay_root() / "config" / "hello_world_job.json",
            overlay_root() / "config" / "hello_world_job.example.json",
        ]
    )
    return candidates


def sample_input_candidates() -> list[Path]:
    root = repo_root()
    env_dir = os.getenv("HELLO_WORLD_SAMPLE_DIR")
    candidates: list[Path] = []

    if env_dir:
        env_path = Path(env_dir)
        candidates.append(env_path / "hello_world_input.json")

    candidates.extend(
        [
            root / "data" / "sample" / "hello_world" / "hello_world_input.json",
            overlay_root() / "data" / "sample" / "hello_world" / "hello_world_input.json",
        ]
    )
    return candidates


def local_data_root() -> Path:
    env_dir = os.getenv("HELLO_WORLD_LOCAL_DATA_DIR")
    if env_dir:
        return Path(env_dir)
    return repo_root() / "data"


def first_existing_path(candidates: list[Path]) -> Path | None:
    for path in candidates:
        if path.is_file():
            return path
    return None


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def load_job_config() -> dict[str, Any]:
    config_path = first_existing_path(config_candidates())
    config = dict(DEFAULT_CONFIG)
    if config_path is None:
        return config

    loaded = load_json(config_path)
    if not isinstance(loaded, dict):
        raise ValueError(f"hello world config must be a JSON object: {config_path}")

    config.update(loaded)
    config["_config_path"] = str(config_path)
    return config


def require_sample_input_path() -> Path:
    sample_path = first_existing_path(sample_input_candidates())
    if sample_path is None:
        searched = "\n".join(str(path) for path in sample_input_candidates())
        raise FileNotFoundError(
            "hello world sample input not found; checked:\n" + searched
        )
    return sample_path


def raw_local_path() -> Path:
    return local_data_root() / "raw" / "hello_world" / "records.json"


def conformed_local_path() -> Path:
    return local_data_root() / "conformed" / "hello_world" / "records.json"


def curated_local_path() -> Path:
    return local_data_root() / "curated" / "hello_world" / "latest" / "summary.json"


def s3_settings() -> dict[str, str] | None:
    endpoint = os.getenv("S3_ENDPOINT_URL") or os.getenv("S3_ENDPOINT")
    access_key = os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("S3_ACCESS_KEY")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY") or os.getenv("S3_SECRET_KEY")
    region = os.getenv("AWS_DEFAULT_REGION") or os.getenv("S3_REGION") or "us-east-1"

    if not endpoint or not access_key or not secret_key:
        return None

    if not endpoint.startswith("http://") and not endpoint.startswith("https://"):
        endpoint = f"http://{endpoint}"

    return {
        "endpoint_url": endpoint,
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key,
        "region_name": region,
    }


def s3_client():
    settings = s3_settings()
    if settings is None:
        return None

    try:
        import boto3  # type: ignore
    except ImportError:
        return None

    return boto3.client("s3", **settings)


def maybe_upload_json(bucket: str, key: str, payload: Any) -> bool:
    client = s3_client()
    if client is None:
        return False

    body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    client.put_object(Bucket=bucket, Key=key, Body=body, ContentType="application/json")
    return True


def maybe_download_json(bucket: str, key: str) -> Any | None:
    client = s3_client()
    if client is None:
        return None

    try:
        response = client.get_object(Bucket=bucket, Key=key)
    except Exception:
        return None

    body = response["Body"].read().decode("utf-8")
    return json.loads(body)
