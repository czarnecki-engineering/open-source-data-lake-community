from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from asx_ohlcv_runtime import fetch_and_publish_raw_ohlcv


DAG_ID = "asx_ohlcv_raw"


with DAG(
    dag_id=DAG_ID,
    description=(
        "Ingests raw ASX OHLCV price data via yFinance into the MinIO raw zone. "
        "First increment: raw ingestion only."
    ),
    schedule=None,
    start_date=datetime(2026, 5, 19),
    catchup=False,
    tags=["solution", "asx_ohlcv", "minio", "raw", "yfinance"],
) as dag:
    PythonOperator(
        task_id="ingest_raw_ohlcv",
        python_callable=fetch_and_publish_raw_ohlcv,
    )
