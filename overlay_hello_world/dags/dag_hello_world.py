from __future__ import annotations

import subprocess
import sys

import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator


def run_script(script_path: str) -> None:
    subprocess.run([sys.executable, script_path], check=True)


with DAG(
    dag_id="dag_hello_world",
    start_date=pendulum.datetime(2026, 1, 1, tz="Australia/Melbourne"),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["hello-world", "reference"],
) as dag:
    local_sample_to_raw = PythonOperator(
        task_id="local_sample_to_raw",
        python_callable=run_script,
        op_args=["/opt/airflow/scripts/hello_world_local_to_raw.py"],
    )

    raw_to_conformed = PythonOperator(
        task_id="raw_to_conformed",
        python_callable=run_script,
        op_args=["/opt/airflow/scripts/hello_world_raw_to_conformed.py"],
    )

    conformed_to_curated = PythonOperator(
        task_id="conformed_to_curated",
        python_callable=run_script,
        op_args=["/opt/airflow/scripts/hello_world_conformed_to_curated.py"],
    )

    local_sample_to_raw >> raw_to_conformed >> conformed_to_curated
