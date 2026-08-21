from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from heartbeat_runtime import publish_curated_heartbeat_summary


DAG_ID = "heartbeat_conformed_to_curated"


with DAG(
    dag_id=DAG_ID,
    description="Deterministic internal heartbeat DAG that publishes a curated latest heartbeat summary into MinIO.",
    schedule=None,
    start_date=datetime(2026, 5, 19),
    catchup=False,
    tags=["solution", "heartbeat", "minio", "curated"],
) as dag:
    PythonOperator(
        task_id="publish_curated_heartbeat_summary",
        python_callable=publish_curated_heartbeat_summary,
    )
