from __future__ import annotations

from datetime import datetime, timedelta, timezone
import io
import os

import boto3
import pandas as pd
import pendulum
import pyarrow as pa
import pyarrow.parquet as pq

from airflow import DAG
from airflow.operators.python import PythonOperator


DATASET_ID = "market_ohlcv_daily"
EXCHANGE = "ASX"

CONFORMED_BUCKET = "conformed"
CURATED_BUCKET = "curated"
MINIO_ENDPOINT = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")


def _s3_client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    )


def _conformed_prefix() -> str:
    return f"tabular/{DATASET_ID}/exchange={EXCHANGE}/"


def _curated_snapshot_key(trade_date: str) -> str:
    return (
        f"tabular/{DATASET_ID}/exchange={EXCHANGE}/trade_date={trade_date}/snapshot.parquet"
    )


def _list_all_objects(s3, bucket: str, prefix: str) -> list[dict]:
    objs: list[dict] = []
    token = None
    while True:
        kwargs = {"Bucket": bucket, "Prefix": prefix}
        if token:
            kwargs["ContinuationToken"] = token
        resp = s3.list_objects_v2(**kwargs)
        objs.extend(resp.get("Contents", []))
        if resp.get("IsTruncated"):
            token = resp.get("NextContinuationToken")
        else:
            break
    return objs


def _trade_dates_in_conformed(s3) -> list[str]:
    # Scan keys once and extract unique trade_date=YYYY-MM-DD
    prefix = _conformed_prefix()
    objs = _list_all_objects(s3, CONFORMED_BUCKET, prefix)

    dates = set()
    for o in objs:
        key = o["Key"]
        if "trade_date=" not in key:
            continue
        # key contains .../trade_date=YYYY-MM-DD/...
        part = key.split("trade_date=", 1)[1]
        trade_date = part.split("/", 1)[0]
        # keep only ISO-looking dates
        if len(trade_date) == 10 and trade_date[4] == "-" and trade_date[7] == "-":
            dates.add(trade_date)

    return sorted(dates)


def _recent_trade_dates(days_back: int = 45) -> list[str]:
    # Use calendar days; conformed only has trading dates anyway.
    today = datetime.now(timezone.utc).date()
    return [(today - timedelta(days=i)).isoformat() for i in range(days_back)]


def build_daily_snapshots(days_back: int = 45) -> None:
    """
    For each recent trade_date, if there is conformed data:
      - read all parquet files for that trade_date
      - dedupe by (dataset_id, exchange, ticker, trade_date)
      - pick latest ingest_ts
      - write curated snapshot.parquet (overwrite is allowed for snapshots)
    """
    s3 = _s3_client()

    if days_back is None:
        trade_dates = _trade_dates_in_conformed(s3)
    else:
        trade_dates = _recent_trade_dates(days_back=days_back)

    #for trade_date in _recent_trade_dates(days_back=days_back):
    for trade_date in trade_dates:
        date_prefix = f"{_conformed_prefix()}trade_date={trade_date}/"
        conformed_objs = [o for o in _list_all_objects(s3, CONFORMED_BUCKET, date_prefix) if o["Key"].endswith(".parquet")]

        if not conformed_objs:
            continue

        # Optional optimisation: only rebuild snapshot if conformed newer than snapshot
        snapshot_key = _curated_snapshot_key(trade_date)
        snapshot_last_modified = None
        try:
            head = s3.head_object(Bucket=CURATED_BUCKET, Key=snapshot_key)
            snapshot_last_modified = head["LastModified"]
        except Exception:
            snapshot_last_modified = None

        latest_conformed = max(o["LastModified"] for o in conformed_objs)
        if snapshot_last_modified and snapshot_last_modified >= latest_conformed:
            continue

        frames: list[pd.DataFrame] = []
        for o in conformed_objs:
            obj = s3.get_object(Bucket=CONFORMED_BUCKET, Key=o["Key"])
            buf = io.BytesIO(obj["Body"].read())
            table = pq.read_table(buf)
            frames.append(table.to_pandas())

        df = pd.concat(frames, ignore_index=True)

        # --- FIX: normalise mixed-type columns before Arrow conversion ---
        def _to_text(v):
            if pd.isna(v):
                return None
            if isinstance(v, (bytes, bytearray)):
                return v.decode("utf-8", errors="replace")
            return str(v)

        # ticker is the one failing; these two are cheap to normalise as well
        if "ticker" in df.columns:
            df["ticker"] = df["ticker"].map(_to_text)
        if "dataset_id" in df.columns:
            df["dataset_id"] = df["dataset_id"].map(_to_text)
        if "exchange" in df.columns:
            df["exchange"] = df["exchange"].map(_to_text)
        # --- end fix ---

        # Ensure ingest_ts sortable
        df["ingest_ts"] = pd.to_datetime(df["ingest_ts"], utc=True, errors="coerce")

        # Latest ingest wins per business key
        df = df.sort_values("ingest_ts", ascending=True)
        df = df.drop_duplicates(
            subset=["dataset_id", "exchange", "ticker", "trade_date"],
            keep="last",
        )

        # Write snapshot
        table = pa.Table.from_pandas(df, preserve_index=False)
        out = io.BytesIO()
        pq.write_table(table, out, compression="snappy")
        out.seek(0)

        s3.put_object(
            Bucket=CURATED_BUCKET,
            Key=snapshot_key,
            Body=out.getvalue(),
            ContentType="application/octet-stream",
        )


with DAG(
    dag_id="asx200_ohlcv_conformed_to_curated_snapshot_v2",
    start_date=pendulum.datetime(2024, 1, 1, tz="Australia/Melbourne"),
    schedule="*/10 * * * *",
    catchup=False,
    max_active_runs=1,
    tags=["minio", "conformed", "curated", "ohlcv", "snapshot"],
) as dag:
    PythonOperator(
        task_id="build_daily_snapshots",
        python_callable=build_daily_snapshots,
        op_kwargs={"days_back": None},
    )
