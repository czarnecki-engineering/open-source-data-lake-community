# Project Context

## Project Overview
- Purpose: local, Docker Compose-based data lake sandbox using MinIO, Airflow, Jupyter, and a small PHP landing page.
- Solution type: single-node, containerised reference stack for ingestion, light transformation, and notebook exploration.

## Repository Scope
- Includes: Docker Compose stack, Airflow DAGs, notebooks, and a small PHP service index.
- Not obviously included: production database for Airflow, monitoring/alerting, CI/CD, cloud infrastructure, or hardened security controls.

## Runtime Architecture
- MinIO: S3-compatible object storage with console and API ports exposed.
- MinIO init: one-off job that creates the `raw`, `conformed`, and `curated` buckets.
- Airflow: single-container webserver + scheduler using `SequentialExecutor` and SQLite metadata.
- Airflow user init: one-off job that creates an admin user if missing.
- Jupyter: minimal notebook server with data science libraries installed.
- PHP: FrankenPHP container serving `php/` as a local service index.

High-level flow: MinIO starts first, buckets are created, Airflow runs DAGs that write to `raw` and transform into `conformed` and `curated`, and Jupyter provides interactive analysis over the resulting objects.

## Key Folders and Files
- `docker-compose.yaml`: primary definition of services and their runtime wiring.
- `docker/airflow/Dockerfile`: custom Airflow image with Python deps.
- `docker/jupyter/Dockerfile`: custom Jupyter image with Python deps.
- `dags/`: Airflow DAGs for heartbeat and ASX OHLCV ingestion/transform.
- `notebooks/`: example notebooks (content is not validated in this repo).
- `php/`: simple PHP landing/health pages served by FrankenPHP.
- `RUNBOOK.md`: step-by-step operational workflow.

## Operational Model
- Intended to run locally with Docker Compose (`docker compose build` then `docker compose up -d`).
- Start order is enforced by dependencies: MinIO -> MinIO init -> Airflow; Jupyter and PHP are independent.
- Airflow uses a local SQLite DB stored in a Docker volume; MinIO data is also stored in a Docker volume.
- ASX OHLCV DAGs require a local `config/asx200_tickers.csv` file to exist and be mounted.

## Evidence Notes
- `docker-compose.yaml` is treated as the primary implementation source for capabilities.
- Some behaviour depends on external services (Yahoo Finance) and local config files, which are not fully proven by the repo alone.
- The PHP service index references several services not present in `docker-compose.yaml` and should not be treated as implemented here.
