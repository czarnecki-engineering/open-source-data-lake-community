from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from heartbeat_runtime import materialize_curated_heartbeat_to_iceberg


DAG_ID = "heartbeat_curated_to_iceberg"


with DAG(
    dag_id=DAG_ID,
    description="Deterministic internal heartbeat DAG that materializes the curated heartbeat summary into the standing Lakekeeper-backed Iceberg path.",
    schedule=None,
    start_date=datetime(2026, 5, 19),
    catchup=False,
    tags=["solution", "heartbeat", "lakekeeper", "iceberg", "trino"],
) as dag:
    PythonOperator(
        task_id="materialize_curated_heartbeat_to_iceberg",
        python_callable=materialize_curated_heartbeat_to_iceberg,
    )
