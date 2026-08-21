from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from asx_ohlcv_runtime import fetch_curated_panel_from_public_source


DAG_ID = "asx_ohlcv_curated_from_public_source"


with DAG(
    dag_id=DAG_ID,
    description=(
        "Community-edition ASX OHLCV ingestion. Downloads a pre-cleaned, "
        "pre-curated panel from a public GitHub repo and writes it straight "
        "into the MinIO curated zone, replacing the yFinance "
        "raw -> raw_to_conformed -> conformed_to_curated chain with a single "
        "step and no external API calls beyond the one-shot GitHub fetch. "
        "asx_ohlcv_curated_to_iceberg reads its output unchanged."
    ),
    schedule=None,
    start_date=datetime(2026, 8, 21),
    catchup=False,
    tags=["solution", "asx_ohlcv", "community", "github-source", "curated"],
) as dag:
    PythonOperator(
        task_id="fetch_curated_panel_from_public_source",
        python_callable=fetch_curated_panel_from_public_source,
    )
