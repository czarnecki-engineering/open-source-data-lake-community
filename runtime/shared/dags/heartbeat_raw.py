from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from heartbeat_runtime import publish_raw_heartbeat


DAG_ID = "heartbeat_raw"


with DAG(
    dag_id=DAG_ID,
    description="Deterministic internal heartbeat DAG that writes one raw heartbeat event into MinIO.",
    schedule=None,
    start_date=datetime(2026, 5, 19),
    catchup=False,
    tags=["solution", "heartbeat", "minio", "raw"],
) as dag:
    PythonOperator(
        task_id="publish_raw_heartbeat",
        python_callable=publish_raw_heartbeat,
    )
