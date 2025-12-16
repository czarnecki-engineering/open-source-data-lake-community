from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import io
import os

import boto3
import pandas as pd
import pendulum
import pyarrow as pa
import pyarrow.parquet as pq

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.context import Context


DATASET_ID = "market_ohlcv_daily"
EXCHANGE = "ASX"

RAW_BUCKET = "raw"
CONFORMED_BUCKET = "conformed"
MINIO_ENDPOINT = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")


def _s3_client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    )


def _raw_prefix() -> str:
    return f"tabular/{DATASET_ID}/exchange={EXCHANGE}/"


def _to_conformed_key(raw_key: str) -> str:
    # raw: .../ticker=ABC.csv -> conformed: same path, .parquet
    if raw_key.endswith(".csv"):
        return raw_key[:-4] + ".parquet"
    return raw_key + ".parquet"


def _row_hash(rec: dict) -> str:
    # Hash the logical row (business key + measures + currency)
    payload = "|".join(
        [
            str(rec.get("dataset_id", "")),
            str(rec.get("exchange", "")),
            str(rec.get("ticker", "")),
            str(rec.get("trade_date", "")),
            str(rec.get("open", "")),
            str(rec.get("high", "")),
            str(rec.get("low", "")),
            str(rec.get("close", "")),
            str(rec.get("volume", "")),
            str(rec.get("currency", "")),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _list_all_keys(s3, bucket: str, prefix: str) -> list[str]:
    keys: list[str] = []
    token = None
    while True:
        kwargs = {"Bucket": bucket, "Prefix": prefix}
        if token:
            kwargs["ContinuationToken"] = token
        resp = s3.list_objects_v2(**kwargs)
        for obj in resp.get("Contents", []):
            keys.append(obj["Key"])
        if resp.get("IsTruncated"):
            token = resp.get("NextContinuationToken")
        else:
            break
    return keys


def convert_new_raw_csvs_to_parquet(**context: Context) -> None:
    s3 = _s3_client()

    raw_keys = [
        k for k in _list_all_keys(s3, RAW_BUCKET, _raw_prefix())
        if k.endswith(".csv")
    ]

    conformed_keys = set(_list_all_keys(s3, CONFORMED_BUCKET, _raw_prefix()))

    ingest_ts = datetime.now(timezone.utc).isoformat()
    ingest_batch_id = context.get("run_id") or ingest_ts

    for raw_key in raw_keys:
        out_key = _to_conformed_key(raw_key)
        if out_key in conformed_keys:
            continue  # append-only: do not overwrite

        obj = s3.get_object(Bucket=RAW_BUCKET, Key=raw_key)
        body = obj["Body"].read()

        df = pd.read_csv(io.BytesIO(body))

        # Expect exactly one row per raw CSV (by design), but handle >1 safely.
        df["ingest_ts"] = ingest_ts
        df["ingest_batch_id"] = ingest_batch_id
        df["source_object_key"] = raw_key

        # Compute row_hash per row
        df["row_hash"] = [
            _row_hash(rec) for rec in df.to_dict(orient="records")
        ]

        table = pa.Table.from_pandas(df, preserve_index=False)

        buf = io.BytesIO()
        pq.write_table(table, buf, compression="snappy")
        buf.seek(0)

        s3.put_object(
            Bucket=CONFORMED_BUCKET,
            Key=out_key,
            Body=buf.getvalue(),
            ContentType="application/octet-stream",
        )


with DAG(
    dag_id="asx200_ohlcv_raw_to_conformed_parquet",
    start_date=pendulum.datetime(2024, 1, 1, tz="Australia/Melbourne"),
    schedule="*/5 * * * *",
    catchup=False,
    max_active_runs=1,
    tags=["minio", "raw", "conformed", "ohlcv"],
) as dag:
    PythonOperator(
        task_id="convert_new_raw_csvs_to_parquet",
        python_callable=convert_new_raw_csvs_to_parquet,
    )
