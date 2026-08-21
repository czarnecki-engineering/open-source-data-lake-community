from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from heartbeat_runtime import publish_conformed_heartbeat


DAG_ID = "heartbeat_raw_to_conformed"


with DAG(
    dag_id=DAG_ID,
    description="Deterministic internal heartbeat DAG that normalizes the latest raw heartbeat event into the conformed zone.",
    schedule=None,
    start_date=datetime(2026, 5, 19),
    catchup=False,
    tags=["solution", "heartbeat", "minio", "conformed"],
) as dag:
    PythonOperator(
        task_id="publish_conformed_heartbeat",
        python_callable=publish_conformed_heartbeat,
    )
