from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from asx_ohlcv_runtime import transform_raw_to_conformed


DAG_ID = "asx_ohlcv_raw_to_conformed"


with DAG(
    dag_id=DAG_ID,
    description=(
        "Normalises raw ASX OHLCV JSON objects from the MinIO raw zone into "
        "conformed records in the MinIO conformed zone."
    ),
    schedule=None,
    start_date=datetime(2026, 5, 19),
    catchup=False,
    tags=["solution", "asx_ohlcv", "minio", "conformed"],
) as dag:
    PythonOperator(
        task_id="transform_raw_to_conformed",
        python_callable=transform_raw_to_conformed,
    )
