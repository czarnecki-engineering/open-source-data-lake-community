# MinIO Test Stack - Project Context

Small, single-node sandbox for exercising S3-style lake patterns with MinIO and a single Airflow container. The stack creates three buckets (`raw`, `conformed`, `curated`) and runs a handful of DAGs that pull OHLCV data from Yahoo Finance, land raw CSVs, convert them to Parquet, and roll daily snapshots.

## Scope and Goals
- Validate local MinIO + Airflow wiring without extra dependencies.
- Demonstrate a minimal raw -> conformed -> curated flow and a heartbeat DAG.
- Keep everything docker-compose-only; no external databases or services required.

## Stack
- **MinIO**: primary S3-compatible store; console on `http://localhost:9001` (user/pass `minioadmin`).
- **MinIO init**: seeds buckets `raw`, `conformed`, `curated` via `mc`.
- **Airflow (single container, SequentialExecutor)**: mounts `./dags`, `./logs`, `./plugins`; installs `yfinance`, `pyarrow`, `pandas` on start.
- **Airflow user init**: creates admin user if missing.

## Data Model and Buckets
- **raw/**: vendor-shaped CSV drops. Examples: `heartbeat/airflow_time_*.txt`; `tabular/market_ohlcv_daily/exchange=ASX/trade_date=YYYY-MM-DD/ticker=TICKER.csv`.
- **conformed/**: schema-aligned Parquet with metadata (`ingest_ts`, `ingest_batch_id`, `row_hash`, `source_object_key`). Paths mirror raw.
- **curated/**: deduped daily snapshots per trade date. Example key: `tabular/market_ohlcv_daily/exchange=ASX/trade_date=YYYY-MM-DD/snapshot.parquet`.

## DAGs (what they do)
- `raw_heartbeat_1m`: every minute write a timestamp text file into `raw/heartbeat/`.
- `raw_market_ohlcv_daily_asx`: every 5 minutes pull recent ASX OHLCV (tickers from `ASX_TICKERS` Airflow Variable, default `BHP,CBA`) and write one CSV per (ticker, trade_date) into `raw/`.
- `raw_to_conformed_copy`: copy new `raw/heartbeat/` objects into `conformed/` (append-only).
- `raw_to_conformed_ohlcv_csv_to_parquet`: convert new raw OHLCV CSVs to Parquet in `conformed/`, add ingest metadata and `row_hash`, skip already converted objects.
- `conformed_to_curated_copy`: copy new `conformed/heartbeat/` objects into `curated/`.
- `conformed_to_curated_ohlcv_daily_snapshot`: build per-day snapshots from conformed Parquet, dedupe on (dataset_id, exchange, ticker, trade_date), keep latest `ingest_ts`, and write/refresh `snapshot.parquet` per date in `curated/`.

## Operation Model
- All state is in Docker volumes and the local `./logs` folder. Re-running `docker compose build airflow && docker compose up -d` from a clean directory is expected.
- Buckets are idempotently created by `minio-init`; DAGs are append-only except the curated snapshot which overwrites per-day snapshots when fresher conformed data exists.

## Environments and Credentials
- Local only; no external cloud endpoints.
- MinIO credentials: `minioadmin` / `minioadmin` (baked into compose and init).
- Airflow admin: `minioadmin` / `minioadmin` (created at container start by `airflow-user-init`).

## Lifecycle
- **Bring up**: build Airflow image (installs deps), create host folders (`dags`, `logs`, `plugins`), then `docker compose up -d`.
- **Tear down**: `docker compose down -v` removes containers and volumes; remove cached Airflow image if you want a clean rebuild.
- **Observability**: use `docker ps --format '{{.Names}}: {{.Status}}' | sort`, Airflow UI (`http://localhost:8080`), and MinIO console (`http://localhost:9001`).
