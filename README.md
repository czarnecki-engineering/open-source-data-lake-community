# Project Name
Open Source Data Lake - Community Edition

# What This Repository Does
Provides a local Docker Compose stack that combines MinIO object storage, Apache Airflow orchestration, a Jupyter notebook environment, and a small PHP service index. The Airflow DAGs demonstrate a simple raw -> conformed -> curated flow using ASX OHLCV data and a heartbeat pipeline.

# Main Components
- MinIO (S3-compatible object storage + console).
- MinIO init job (creates `raw`, `conformed`, `curated` buckets).
- Apache Airflow (single-container webserver + scheduler, SequentialExecutor, SQLite metadata DB).
- Jupyter (minimal notebook server with common data libraries).
- PHP (FrankenPHP container serving `php/` as a simple service index).

# Prerequisites
- Docker Engine
- Docker Compose v2 (`docker compose`)

# How to Run
The canonical local workflow is in `RUNBOOK.md`. In brief, from the repo root:

1. Create `config/asx200_tickers.csv` (see `config/asx200_tickers_top3.csv` or `config/asx200_tickers_top100.csv` as examples).
2. Create a local `.env` file from the template before starting the stack:

```bash
cp .env.example .env
```

3. Start the stack:

```bash
./start-compose.sh
```

This script builds the local images and starts the Docker Compose stack in detached mode.

To stop the stack:

```bash
./stop-compose.sh
```

This stops and removes the containers while preserving Docker volumes and your persisted local data.

To stop the stack and remove persisted Compose data:

```bash
./stop-compose.sh --volumes
```

This performs a full local reset of the stack's Docker volumes. Use it when you want to clear Airflow state and MinIO data.

If any step fails, follow the detailed operational guidance in `RUNBOOK.md`.

### Environment Configuration

Docker Compose automatically reads `.env` from the repository root if the file is present.

`.env.example` is a template only. It is not loaded automatically and is provided as a starting point for a local `.env` file:

```bash
cp .env.example .env
```

Configuration precedence:

1. Shell environment variables
2. `.env` file

`.env.example` contains placeholder/demo values only. Do not commit `.env`, and replace placeholders with real credentials only when an external integration requires them.

Kaggle credentials are required only when running the Kaggle overlay.

Some settings, such as the Airflow executor, S3 endpoint, and internal service configuration, are not exposed via `.env` and require editing `docker-compose.yaml`.

# Reset Modes

## Normal stop

```bash
./stop-compose.sh
```

Use this for ordinary shutdown. Containers are removed, but Docker volumes are preserved.

What stays:
- MinIO bucket contents in `minio-data`
- Airflow metadata database in `airflow-db`
- Git-tracked local files such as `config/`, `dags/`, `notebooks/`, and `php/`
- Host bind-mounted directories such as `logs/` and `plugins/`

## Full reset

```bash
./stop-compose.sh --volumes
```

Use this when you want a clean local reset. This removes the stack containers and the Compose volumes.

What is deleted:
- MinIO objects and bucket data stored in `minio-data`
- Airflow metadata and history stored in `airflow-db`

What is not deleted:
- Repository files in the working tree
- `config/asx200_tickers.csv`
- Files under bind-mounted directories such as `notebooks/`, `php/`, `dags/`, `logs/`, and `plugins/`

# Manual Ticker Configuration (ASX Data Pipeline)
- The ASX ingestion DAG `asx200_ohlcv_daily_to_raw` requires a local configuration file: `config/asx200_tickers.csv`.
- This file is not provided by default and must be created manually by the operator.
- Purpose: control the number of tickers queried from yFinance and avoid excessive or abusive API usage.
- Behaviour:
  - If the file is missing, the DAG will fail.
  - This is expected and does not indicate a problem with the platform.
- The platform is considered healthy if:
  - services start successfully,
  - the Airflow UI is accessible,
  - heartbeat DAGs are running.
- Sample starting points are available in `config/asx200_tickers_top3.csv` and `config/asx200_tickers_top100.csv`.

# What to Expect When Running
- Airflow UI: `http://localhost:8080` (user/password are both `admin`).
- MinIO Console: `http://localhost:9001` (user/password are both `minioadmin`).
- MinIO S3 API: `http://localhost:9000`.
- Jupyter: `http://localhost:8888` (token is `jupyter`).
- PHP service index: `http://localhost:8088`.

MinIO buckets `raw`, `conformed`, and `curated` are created automatically by the init container. Airflow DAGs write and transform data inside those buckets.

## DAG Execution Model

- Heartbeat DAGs run automatically and provide the system health signal.
- ASX DAGs do not run automatically and must be triggered manually via the Airflow UI.
- Run the ASX pipeline in sequence:
  1. `asx200_ohlcv_daily_to_raw`
  2. `asx200_ohlcv_raw_to_conformed_parquet`
  3. `asx200_ohlcv_conformed_to_curated_snapshot_v2`
- The ASX backfill DAG is manual-trigger only and should be run when required.
- Absence of ASX data does not indicate platform failure.
- Heartbeat DAGs are the indicator of platform health.

# Data Persistence

Local persistence is split between Docker volumes and bind-mounted repository folders.

- Docker volume `minio-data`: stores MinIO bucket contents for `raw`, `conformed`, and `curated`
- Docker volume `airflow-db`: stores the Airflow SQLite metadata database and scheduler/web state
- Bind mount `./notebooks`: notebook files remain in the repository working tree
- Bind mount `./php`: PHP files remain in the repository working tree
- Bind mounts `./dags`, `./config`, `./logs`, and `./plugins`: remain on disk in the repository

Practical rule:
- `./stop-compose.sh` preserves Docker-volume data
- `./stop-compose.sh --volumes` deletes Docker-volume data
- Neither command deletes Git-tracked repository content

# Repository Structure
- `docker-compose.yaml`: service definitions and runtime wiring.
- `docker/`: Dockerfiles for Airflow and Jupyter.
- `dags/`: Airflow DAGs (heartbeat, ASX OHLCV ingestion, raw->conformed, conformed->curated).
- `config/`: CSV ticker config required by ASX DAGs.
- `notebooks/`: example notebooks for exploration.
- `php/`: simple PHP landing/health pages.

# Related Documentation
- `docs/internal/PROJECT_CONTEXT.md`
- `RUNBOOK.md`
- `docs/reference/CONTENTS.md`
- `docs/internal/TODO.md`

# Current Status / Notes
- The ASX OHLCV DAGs depend on a local `config/asx200_tickers.csv` file; without it they will fail.
- Airflow uses SQLite and SequentialExecutor in a single container, which is suited to local demos only.
- The PHP landing page references other services (e.g., Metabase, ClickHouse) that are not present in `docker-compose.yaml`.
