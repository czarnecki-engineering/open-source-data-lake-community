from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib import error, request


LOGGER = logging.getLogger(__name__)

MINIO_ENDPOINT = "http://minio:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_REGION = "local-01"

RAW_BUCKET = "raw"
RAW_PREFIX = "reference/heartbeat/events"
CONFORMED_BUCKET = "conformed"
CONFORMED_PREFIX = "reference/heartbeat/events"
CURATED_BUCKET = "curated"
CURATED_KEY = "reference/heartbeat/latest/heartbeat_summary.json"

AIRFLOW_CONFIG_PATH = Path("/opt/airflow/config/dags/heartbeat.json")

BASE_URL = "http://lakekeeper:8181"
CATALOG_URI = f"{BASE_URL}/catalog"
WAREHOUSE_NAME = "minio-spike"
WAREHOUSE_BUCKET = "curated"
WAREHOUSE_PREFIX = "lakekeeper-spike"
NAMESPACE_NAME = "demo"
TABLE_NAME = "heartbeat_events"
TABLE_IDENTIFIER = (NAMESPACE_NAME, TABLE_NAME)
VENDORED_PACKAGES_PATH = Path("/opt/airflow/vendor")

WAREHOUSE_CREATE_PAYLOAD = {
    "warehouse-name": WAREHOUSE_NAME,
    "storage-profile": {
        "type": "s3",
        "bucket": WAREHOUSE_BUCKET,
        "key-prefix": WAREHOUSE_PREFIX,
        "endpoint": f"{MINIO_ENDPOINT}/",
        "region": MINIO_REGION,
        "path-style-access": True,
        "sts-enabled": False,
        "flavor": "s3-compat",
        "push-s3-delete-disabled": True,
        "remote-signing-enabled": False,
    },
    "storage-credential": {
        "type": "s3",
        "credential-type": "access-key",
        "access-key-id": MINIO_ACCESS_KEY,
        "secret-access-key": MINIO_SECRET_KEY,
    },
}


def load_heartbeat_config() -> dict[str, str]:
    candidate = AIRFLOW_CONFIG_PATH
    if not candidate.is_file():
        raise RuntimeError(
            "Heartbeat config was not found at the canonical Airflow path "
            f"{candidate}."
        )

    payload = json.loads(candidate.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Heartbeat config at {candidate} was not a JSON object.")

    interval = str(payload.get("interval", "")).strip()
    message_format = str(payload.get("message_format", "")).strip()
    if interval == "":
        raise RuntimeError(f"Heartbeat config at {candidate} had an empty interval.")
    if message_format == "":
        raise RuntimeError(f"Heartbeat config at {candidate} had an empty message_format.")

    return {
        "interval": interval,
        "message_format": message_format,
        "config_path": str(candidate),
    }


def _utc_iso(dt: datetime) -> str:
    return dt.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def execution_timestamp(context: dict[str, Any]) -> datetime:
    for key in ("data_interval_end", "logical_date", "ts"):
        value = context.get(key)
        if isinstance(value, datetime):
            return value.astimezone(UTC).replace(second=0, microsecond=0)

    return datetime.now(UTC).replace(second=0, microsecond=0)


def heartbeat_filename(ts: datetime) -> str:
    return f"heartbeat_{ts.strftime('%Y%m%dT%H%M%SZ')}.json"


def raw_key_for_timestamp(ts: datetime) -> str:
    return f"{RAW_PREFIX}/{ts.strftime('%Y-%m-%d')}/{heartbeat_filename(ts)}"


def conformed_key_for_timestamp(ts: datetime) -> str:
    return f"{CONFORMED_PREFIX}/{ts.strftime('%Y-%m-%d')}/{heartbeat_filename(ts)}"


def _load_boto3() -> Any:
    import sys

    vendored = str(VENDORED_PACKAGES_PATH)
    if vendored not in sys.path:
        sys.path.insert(0, vendored)

    import boto3

    return boto3


def get_s3_client() -> Any:
    boto3 = _load_boto3()
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name=MINIO_REGION,
    )


def put_json_object(bucket: str, key: str, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    s3 = get_s3_client()
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType="application/json",
    )
    LOGGER.info("Published JSON object to s3://%s/%s.", bucket, key)


def load_json_object(bucket: str, key: str) -> dict[str, Any]:
    s3 = get_s3_client()
    response = s3.get_object(Bucket=bucket, Key=key)
    payload = response["Body"].read()
    if not payload:
        raise RuntimeError(f"Expected non-empty JSON object at s3://{bucket}/{key}.")
    decoded = json.loads(payload.decode("utf-8"))
    if not isinstance(decoded, dict):
        raise RuntimeError(f"Expected JSON object at s3://{bucket}/{key}.")
    return decoded


def find_latest_json_object(bucket: str, prefix: str) -> tuple[str, dict[str, Any]]:
    s3 = get_s3_client()
    paginator = s3.get_paginator("list_objects_v2")
    latest: dict[str, Any] | None = None

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for item in page.get("Contents", []):
            key = item.get("Key")
            if not isinstance(key, str) or not key.endswith(".json"):
                continue
            if latest is None or key > latest["Key"]:
                latest = item

    if latest is None:
        raise RuntimeError(f"No JSON objects found under s3://{bucket}/{prefix}.")

    key = latest["Key"]
    return key, load_json_object(bucket, key)


def build_raw_event(context: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    config = load_heartbeat_config()
    ts = execution_timestamp(context)
    key = raw_key_for_timestamp(ts)
    event_timestamp = _utc_iso(ts)
    payload = {
        "event_id": ts.strftime("%Y%m%dT%H%M%SZ"),
        "generated_at": _utc_iso(datetime.now(UTC)),
        "interval": config["interval"],
        "message_format": config["message_format"],
        "message": config["message_format"].format(timestamp=event_timestamp),
        "event_timestamp": event_timestamp,
        "config_path": config["config_path"],
        "raw_bucket": RAW_BUCKET,
        "raw_key": key,
        "raw_uri": f"s3://{RAW_BUCKET}/{key}",
        "source": "knowledge-lake-heartbeat",
    }
    return key, payload


def publish_raw_heartbeat(**context: Any) -> None:
    key, payload = build_raw_event(context)
    put_json_object(RAW_BUCKET, key, payload)


def publish_conformed_heartbeat() -> None:
    raw_key, raw_payload = find_latest_json_object(RAW_BUCKET, RAW_PREFIX)
    event_timestamp = datetime.fromisoformat(
        raw_payload["event_timestamp"].replace("Z", "+00:00")
    ).astimezone(UTC)
    conformed_key = conformed_key_for_timestamp(event_timestamp)

    payload = {
        "event_id": raw_payload["event_id"],
        "generated_at": _utc_iso(datetime.now(UTC)),
        "interval": raw_payload["interval"],
        "message": raw_payload["message"],
        "message_format": raw_payload["message_format"],
        "event_timestamp": raw_payload["event_timestamp"],
        "normalized_at": _utc_iso(datetime.now(UTC)),
        "raw_bucket": RAW_BUCKET,
        "raw_key": raw_key,
        "raw_uri": f"s3://{RAW_BUCKET}/{raw_key}",
        "conformed_bucket": CONFORMED_BUCKET,
        "conformed_key": conformed_key,
        "conformed_uri": f"s3://{CONFORMED_BUCKET}/{conformed_key}",
        "config_path": raw_payload.get("config_path", "unknown"),
        "source": raw_payload.get("source", "knowledge-lake-heartbeat"),
    }
    put_json_object(CONFORMED_BUCKET, conformed_key, payload)


def publish_curated_heartbeat_summary() -> None:
    conformed_key, conformed_payload = find_latest_json_object(
        CONFORMED_BUCKET,
        CONFORMED_PREFIX,
    )

    payload = {
        "generated_at": _utc_iso(datetime.now(UTC)),
        "source_event_count": 1,
        "event_id": conformed_payload["event_id"],
        "interval": conformed_payload["interval"],
        "latest_message": conformed_payload["message"],
        "latest_event_timestamp": conformed_payload["event_timestamp"],
        "config_path": conformed_payload.get("config_path", "unknown"),
        "raw_prefix": f"s3://{RAW_BUCKET}/{RAW_PREFIX}/",
        "conformed_prefix": f"s3://{CONFORMED_BUCKET}/{CONFORMED_PREFIX}/",
        "raw_uri": conformed_payload["raw_uri"],
        "conformed_uri": f"s3://{CONFORMED_BUCKET}/{conformed_key}",
        "curated_object": f"s3://{CURATED_BUCKET}/{CURATED_KEY}",
        "curated_bucket": CURATED_BUCKET,
        "curated_key": CURATED_KEY,
        "table_identifier": f"{NAMESPACE_NAME}.{TABLE_NAME}",
        "expected_trino_query": (
            f"SELECT event_id, latest_event_timestamp, latest_message "
            f"FROM {NAMESPACE_NAME}.{TABLE_NAME} "
            f"ORDER BY latest_event_timestamp DESC LIMIT 20"
        ),
        "iceberg_materialization_dag": "heartbeat_curated_to_iceberg",
        "notebook_summary_path": "/home/jovyan/data/heartbeat_summary.json",
    }
    put_json_object(CURATED_BUCKET, CURATED_KEY, payload)


def _request_json(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    expected_statuses: tuple[int, ...] = (200,),
) -> tuple[int, dict[str, Any] | list[Any] | None]:
    url = f"{BASE_URL}{path}"
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    req = request.Request(url=url, data=body, headers=headers, method=method)

    try:
        with request.urlopen(req, timeout=30) as response:
            raw_body = response.read().decode("utf-8")
            parsed = json.loads(raw_body) if raw_body else None
            if response.status not in expected_statuses:
                raise RuntimeError(
                    f"Unexpected Lakekeeper status for {method} {path}: {response.status}"
                )
            return response.status, parsed
    except error.HTTPError as exc:
        raw_body = exc.read().decode("utf-8")
        parsed = None
        if raw_body:
            try:
                parsed = json.loads(raw_body)
            except json.JSONDecodeError:
                parsed = None
        exc.lakekeeper_error_payload = parsed
        raise


def _bootstrap_catalog() -> None:
    _request_json(
        "POST",
        "/management/v1/bootstrap",
        payload={"accept-terms-of-use": True},
        expected_statuses=(204,),
    )


def _is_project_not_found_error(exc: error.HTTPError) -> bool:
    payload = getattr(exc, "lakekeeper_error_payload", None) or {}
    return exc.code == 404 and payload.get("error", {}).get("type") == "ProjectNotFound"


def _find_warehouse(warehouses: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    for warehouse in warehouses:
        if warehouse.get("name") == name:
            return warehouse
    return None


def _create_warehouse() -> dict[str, Any]:
    try:
        _, warehouse_payload = _request_json(
            "POST",
            "/management/v1/warehouse",
            payload=WAREHOUSE_CREATE_PAYLOAD,
            expected_statuses=(201,),
        )
    except error.HTTPError as exc:
        if not _is_project_not_found_error(exc):
            raise
        _bootstrap_catalog()
        _, warehouse_payload = _request_json(
            "POST",
            "/management/v1/warehouse",
            payload=WAREHOUSE_CREATE_PAYLOAD,
            expected_statuses=(201,),
        )

    if not isinstance(warehouse_payload, dict):
        raise RuntimeError("Lakekeeper create warehouse response was not a JSON object.")
    return warehouse_payload


def ensure_warehouse() -> str:
    _, warehouses_payload = _request_json("GET", "/management/v1/warehouse")
    warehouses = (
        warehouses_payload.get("warehouses", [])
        if isinstance(warehouses_payload, dict)
        else []
    )
    warehouse = _find_warehouse(warehouses, WAREHOUSE_NAME)
    if warehouse is None:
        warehouse = _create_warehouse()
    warehouse_id = warehouse.get("warehouse-id")
    if not warehouse_id:
        raise RuntimeError("Lakekeeper warehouse response did not include warehouse-id.")
    return warehouse_id


def ensure_namespace(warehouse_id: str) -> None:
    _, namespaces_payload = _request_json("GET", f"/catalog/v1/{warehouse_id}/namespaces")
    namespaces = (
        namespaces_payload.get("namespaces", [])
        if isinstance(namespaces_payload, dict)
        else []
    )
    namespace_names = {tuple(namespace) for namespace in namespaces}

    if (NAMESPACE_NAME,) not in namespace_names:
        _request_json(
            "POST",
            f"/catalog/v1/{warehouse_id}/namespaces",
            payload={"namespace": [NAMESPACE_NAME]},
            expected_statuses=(200,),
        )


def _load_catalog_client() -> Any:
    import sys

    vendored = str(VENDORED_PACKAGES_PATH)
    if vendored not in sys.path:
        sys.path.insert(0, vendored)

    from pyiceberg.catalog import load_catalog

    return load_catalog(
        "lakekeeper",
        **{
            "type": "rest",
            "uri": CATALOG_URI,
            "warehouse": WAREHOUSE_NAME,
            "s3.endpoint": MINIO_ENDPOINT,
            "s3.access-key-id": MINIO_ACCESS_KEY,
            "s3.secret-access-key": MINIO_SECRET_KEY,
            "s3.region": MINIO_REGION,
        },
    )


def _create_heartbeat_table(catalog: Any) -> Any:
    from pyiceberg.schema import Schema
    from pyiceberg.types import LongType, NestedField, StringType

    schema = Schema(
        NestedField(field_id=1, name="event_id", field_type=StringType(), required=False),
        NestedField(field_id=2, name="generated_at", field_type=StringType(), required=False),
        NestedField(
            field_id=3,
            name="latest_event_timestamp",
            field_type=StringType(),
            required=False,
        ),
        NestedField(field_id=4, name="interval", field_type=StringType(), required=False),
        NestedField(field_id=5, name="latest_message", field_type=StringType(), required=False),
        NestedField(field_id=6, name="raw_uri", field_type=StringType(), required=False),
        NestedField(field_id=7, name="conformed_uri", field_type=StringType(), required=False),
        NestedField(field_id=8, name="curated_uri", field_type=StringType(), required=False),
        NestedField(field_id=9, name="config_path", field_type=StringType(), required=False),
        NestedField(field_id=10, name="source_event_count", field_type=LongType(), required=False),
    )
    return catalog.create_table(TABLE_IDENTIFIER, schema=schema)


def _table_contains_event(table: Any, event_id: str) -> bool:
    snapshots = table.metadata.snapshots or []
    if not snapshots:
        return False

    try:
        existing = table.scan().to_arrow()
    except Exception as exc:  # pragma: no cover - runtime-only defensive logging
        LOGGER.warning(
            "Unable to inspect existing heartbeat rows before append; proceeding without dedupe. event_id=%s error=%s",
            event_id,
            exc,
        )
        return False

    if "event_id" not in existing.column_names:
        return False

    return event_id in set(existing["event_id"].to_pylist())


def materialize_curated_heartbeat_to_iceberg() -> None:
    import sys

    vendored = str(VENDORED_PACKAGES_PATH)
    if vendored not in sys.path:
        sys.path.insert(0, vendored)

    from pyiceberg.exceptions import NoSuchTableError
    import pyarrow as pa

    curated = load_json_object(CURATED_BUCKET, CURATED_KEY)
    warehouse_id = ensure_warehouse()
    ensure_namespace(warehouse_id)
    catalog = _load_catalog_client()

    try:
        table = catalog.load_table(TABLE_IDENTIFIER)
    except NoSuchTableError:
        table = _create_heartbeat_table(catalog)

    row = {
        "event_id": curated["event_id"],
        "generated_at": curated["generated_at"],
        "latest_event_timestamp": curated["latest_event_timestamp"],
        "interval": curated["interval"],
        "latest_message": curated["latest_message"],
        "raw_uri": curated["raw_uri"],
        "conformed_uri": curated["conformed_uri"],
        "curated_uri": curated["curated_object"],
        "config_path": curated.get("config_path", "unknown"),
        "source_event_count": int(curated["source_event_count"]),
    }

    if _table_contains_event(table, row["event_id"]):
        LOGGER.info(
            "Heartbeat event %s is already present in %s.%s; leaving table unchanged.",
            row["event_id"],
            NAMESPACE_NAME,
            TABLE_NAME,
        )
    else:
        table.append(pa.Table.from_pylist([row]))
        LOGGER.info(
            "Appended heartbeat event %s into %s.%s.",
            row["event_id"],
            NAMESPACE_NAME,
            TABLE_NAME,
        )

    table = catalog.load_table(TABLE_IDENTIFIER)
    metadata_location = table.metadata_location
    if not metadata_location:
        raise RuntimeError("Heartbeat Iceberg table did not expose a metadata location.")

    LOGGER.info(
        "Heartbeat Iceberg materialization succeeded for %s.%s with metadata at %s.",
        NAMESPACE_NAME,
        TABLE_NAME,
        metadata_location,
    )
