# Implemented Capabilities

## Summary
This file lists capabilities evidenced directly by the repository, with `docker-compose.yaml` treated as the primary implementation source.

## Capabilities Confirmed by Repository Evidence

| Capability Area | Capability | Evidence | Confidence | Notes |
| --- | --- | --- | --- | --- |
| Containerisation | Local Docker Compose stack | `docker-compose.yaml`, `RUNBOOK.md` | High | Single-node, local-only composition. |
| Storage | S3-compatible object storage (MinIO) | `docker-compose.yaml` | High | API on 9000, console on 9001. |
| Storage | Automatic bucket init (`raw`, `conformed`, `curated`) | `docker-compose.yaml` (minio-init) | High | Uses `minio/mc` to create buckets. |
| Orchestration | Airflow webserver + scheduler | `docker-compose.yaml` | High | Single container, `SequentialExecutor`, SQLite metadata DB. |
| Data Ingestion | ASX OHLCV ingestion from Yahoo Finance | `dags/asx200_ohlcv_daily_to_raw.py` | High | Writes raw CSVs into MinIO. |
| Data Processing | Raw CSV -> conformed Parquet conversion | `dags/asx200_ohlcv_raw_to_conformed_parquet.py` | High | Adds ingest metadata and row hash. |
| Data Processing | Conformed -> curated daily snapshots | `dags/asx200_ohlcv_conformed_to_curated_snapshot_v2.py` | High | Dedupes by business key and overwrites per-date snapshots. |
| Workflow Management | Heartbeat pipeline (raw -> conformed -> curated) | `dags/heartbeat_1m_to_raw.py`, `dags/heartbeat_1m_copy_raw_to_conformed.py`, `dags/heartbeat_1m_copy_conformed_to_curated.py` | High | Provides a simple pipeline signal. |
| Notebook / Interactive Analysis | Jupyter notebook server | `docker-compose.yaml`, `docker/jupyter/Dockerfile` | High | Exposes 8888 with a fixed token. |
| Developer Utilities | PHP service index | `docker-compose.yaml`, `php/index.php` | High | Simple landing page in FrankenPHP. |
| Libraries / Tooling | Data libraries in Airflow and Jupyter images | `docker/airflow/Dockerfile`, `docker/jupyter/Dockerfile` | High | Includes pandas, pyarrow; Airflow also has yfinance. |

## Capabilities Present but Partially Evidenced
- ASX200 backfill DAG exists, but depends on bucket-based control files and state that are not provided in the repo (`dags/asx200_ohlcv_backfill_to_raw.py`).
- Notebook content is present, but not validated against actual runtime data in this repo (`notebooks/`).
- Airflow plugins directory is mounted but has no implemented plugins (`plugins/`).

## Capabilities Not Evidenced
- External databases for Airflow (e.g., Postgres) or analytics engines.
- Monitoring, alerting, or metrics pipelines.
- Authentication/authorization beyond default service credentials.
- Data catalog, lineage, or governance tooling.
- HA, scaling, or production hardening features.
- Additional analytics or LLM support services beyond the current Airflow, MinIO, Jupyter, and PHP stack.

## Notes for Tier Mapping
- Safe to claim: local MinIO storage, Airflow orchestration, Jupyter notebooks, and basic raw->conformed->curated flows.
- Phrase cautiously: ASX backfill workflows and notebook outcomes; they depend on external data and local config.
- Do not claim: production readiness, monitoring/alerting, governance, or services beyond the current compose stack.
