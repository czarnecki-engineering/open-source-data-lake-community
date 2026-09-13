from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from asx_ohlcv_runtime import summarise_conformed_to_curated


DAG_ID = "asx_ohlcv_conformed_to_curated"


with DAG(
    dag_id=DAG_ID,
    description=(
        "Aggregates conformed ASX OHLCV records from the MinIO conformed zone into "
        "a per-run curated summary in the MinIO curated zone."
    ),
    schedule=None,
    start_date=datetime(2026, 5, 19),
    catchup=False,
    tags=["solution", "asx_ohlcv", "minio", "curated"],
) as dag:
    PythonOperator(
        task_id="summarise_conformed_to_curated",
        python_callable=summarise_conformed_to_curated,
    )
