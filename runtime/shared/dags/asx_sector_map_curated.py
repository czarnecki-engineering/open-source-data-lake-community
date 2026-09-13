from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from asx_sector_map_runtime import publish_curated_sector_map


DAG_ID = "asx_sector_map_curated"


with DAG(
    dag_id=DAG_ID,
    description=(
        "Builds the ASX ticker sector reference map from Yahoo Finance metadata "
        "and publishes it to the MinIO curated zone."
    ),
    schedule=None,
    start_date=datetime(2026, 5, 19),
    catchup=False,
    tags=["solution", "asx", "sector_map", "minio", "curated", "yfinance"],
) as dag:
    PythonOperator(
        task_id="publish_curated_sector_map",
        python_callable=publish_curated_sector_map,
    )
