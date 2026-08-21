from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from asx_ohlcv_runtime import materialise_curated_asx_ohlcv_to_iceberg


DAG_ID = "asx_ohlcv_curated_to_iceberg"


with DAG(
    dag_id=DAG_ID,
    description=(
        "Materialises the curated ASX OHLCV summary into the standing "
        "Lakekeeper-backed Iceberg table and validates Trino query access."
    ),
    schedule=None,
    start_date=datetime(2026, 5, 19),
    catchup=False,
    tags=["solution", "asx_ohlcv", "lakekeeper", "iceberg", "trino"],
) as dag:
    PythonOperator(
        task_id="materialise_curated_asx_ohlcv_to_iceberg",
        python_callable=materialise_curated_asx_ohlcv_to_iceberg,
    )
