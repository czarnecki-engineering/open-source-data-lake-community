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
The canonical steps are in `RUNBOOK.md`. In brief, from the repo root:

1) Create `config/asx200_tickers.csv` (see `config/asx200_tickers_top3.csv` or `config/asx200_tickers_top100.csv` as examples).
2) Build images: `docker compose build`
3) Start services: `docker compose up -d`

If any step fails, follow the detailed teardown/rebuild flow in `RUNBOOK.md`.

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
- Airflow UI: `http://localhost:8080` (user/password are both `minioadmin`).
- MinIO Console: `http://localhost:9001` (user/password are both `minioadmin`).
- MinIO S3 API: `http://localhost:9000`.
- Jupyter: `http://localhost:8888` (token is `jupyter`).
- PHP service index: `http://localhost:8088`.

MinIO buckets `raw`, `conformed`, and `curated` are created automatically by the init container. Airflow DAGs write and transform data inside those buckets.

# Repository Structure
- `docker-compose.yaml`: service definitions and runtime wiring.
- `docker/`: Dockerfiles for Airflow and Jupyter.
- `dags/`: Airflow DAGs (heartbeat, ASX OHLCV ingestion, raw->conformed, conformed->curated).
- `config/`: CSV ticker config required by ASX DAGs.
- `notebooks/`: example notebooks for exploration.
- `php/`: simple PHP landing/health pages.

# Related Documentation
- `PROJECT_CONTEXT.md`
- `RUNBOOK.md`
- `CONTENTS.md`
- `TODO.md`

# Current Status / Notes
- The ASX OHLCV DAGs depend on a local `config/asx200_tickers.csv` file; without it they will fail.
- Airflow uses SQLite and SequentialExecutor in a single container, which is suited to local demos only.
- The PHP landing page references other services (e.g., Metabase, ClickHouse) that are not present in `docker-compose.yaml`.
