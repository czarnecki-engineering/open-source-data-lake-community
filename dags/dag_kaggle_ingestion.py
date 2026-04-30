from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator


REPO_ROOT = Path(os.getenv("OPEN_DATA_LAKE_REPO_ROOT", "/opt/airflow"))
CONFIG_PATH = os.getenv("KAGGLE_JOBS_CONFIG", str(REPO_ROOT / "config" / "kaggle_jobs.json"))
JOB_NAME = os.getenv("KAGGLE_JOB_NAME")


def _run_script(script_name: str) -> None:
    script_path = REPO_ROOT / "scripts" / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    command = [sys.executable, str(script_path), "--config", CONFIG_PATH]
    if JOB_NAME:
        command.extend(["--job", JOB_NAME])
    if script_name == "kaggle_to_raw.py":
        command.append("--replace")

    subprocess.run(command, check=True, cwd=str(REPO_ROOT), env=os.environ.copy())


def run_kaggle_to_raw() -> None:
    _run_script("kaggle_to_raw.py")


def run_raw_to_conformed() -> None:
    _run_script("raw_to_conformed.py")


def run_conformed_to_curated() -> None:
    _run_script("conformed_to_curated.py")


with DAG(
    dag_id="dag_kaggle_ingestion",
    start_date=pendulum.datetime(2024, 1, 1, tz="Australia/Melbourne"),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["kaggle", "overlay", "raw", "conformed", "curated"],
) as dag:
    kaggle_to_raw = PythonOperator(
        task_id="kaggle_to_raw",
        python_callable=run_kaggle_to_raw,
    )

    raw_to_conformed = PythonOperator(
        task_id="raw_to_conformed",
        python_callable=run_raw_to_conformed,
    )

    conformed_to_curated = PythonOperator(
        task_id="conformed_to_curated",
        python_callable=run_conformed_to_curated,
    )

    kaggle_to_raw >> raw_to_conformed >> conformed_to_curated
