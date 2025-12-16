# Architecture Summary

Summarized from `docs/source/chat-airflow.md` (ChatGPT architectural discussion). Focus: components configured and the two pipelines (heartbeat, yFinance OHLCV).

## Components
- **MinIO**: S3-compatible store; console on port 9001. Buckets: `raw`, `conformed`, `curated`. Credentials fixed to `minioadmin` / `minioadmin`. Data lives in Docker volume `minio-data`.
- **minio-init**: one-shot job that sets the alias and creates buckets `raw`, `conformed`, `curated` (idempotent).
- **Airflow (single container)**: SequentialExecutor + SQLite (`/opt/airflow/airflow.db` on volume `airflow-db`). Mounts `./dags`, `./logs`, `./plugins`. Installs `yfinance`, `pyarrow`, `pandas` via Dockerfile/custom image. Airflow UI on port 8080.
- **airflow-user-init**: one-shot init container (same image) that runs `airflow db migrate` and creates admin user `minioadmin` / `minioadmin` against the shared SQLite DB. Depends on `airflow` service start.

## Design Approach
- Keep the stack minimal and local: Docker Compose only, single Airflow container, SQLite metadata, no external DB.
- Hard-code MinIO endpoint/creds in compose and DAG env to simplify S3-compatible access.
- Idempotent bucket creation and user creation so repeated brings are stable.
- DAG design favors append-only writes; curated snapshots overwrite per-day snapshot files only when fresher conformed data exists.
- Copy DAGs are narrowed to explicit prefixes to avoid propagating unwanted object types across buckets.
- Conformed is append-only; curated is where dedupe or latest-wins logic happens.
- Change detection is via scheduled scans (list/prefix) rather than bucket notifications; eventing left for later.
- Healthchecks: webserver `/health` determines Airflow container health; MinIO is waited on by `minio-init`.

## Pipelines
### Heartbeat pipeline
- **Source DAG**: `raw_heartbeat_1m` writes timestamp `.txt` to `raw/heartbeat/` every minute.
- **Promotion DAGs**: `raw_to_conformed_copy` copies only objects under `raw/heartbeat/` into `conformed/heartbeat/`; `conformed_to_curated_copy` copies only objects under `conformed/heartbeat/` into `curated/heartbeat/`.
- **Intent**: proves S3 connectivity and bucket propagation without touching other datasets.

### yFinance OHLCV pipeline (ASX)
- **Ingest (raw)**: `raw_market_ohlcv_daily_asx`
  - Schedule: every 5 minutes.
  - Tickers: from Airflow Variable `ASX_TICKERS` (default `BHP,CBA`).
  - Action: download recent OHLCV via `yfinance`; write one CSV per `(ticker, trade_date)` to `raw/tabular/market_ohlcv_daily/exchange=ASX/trade_date=YYYY-MM-DD/ticker=TICKER.csv`.
- **Transform (conformed)**: `raw_to_conformed_ohlcv_csv_to_parquet`
  - Reads raw CSVs.
  - Writes Parquet to `conformed/` with added metadata: `ingest_ts`, `ingest_batch_id`, `row_hash`, `source_object_key`.
  - Append-only: skips objects already converted.
- **Curate (snapshot)**: `conformed_to_curated_ohlcv_daily_snapshot`
  - For recent trade dates, reads Parquet from `conformed/`, dedupes on `(dataset_id, exchange, ticker, trade_date)` keeping latest `ingest_ts`, and writes/refreshes `snapshot.parquet` per date to `curated/tabular/.../trade_date=YYYY-MM-DD/snapshot.parquet`.
- **Copy DAG constraints**: Copy DAGs are not used for OHLCV data; they are scoped to heartbeat prefix to prevent CSV bleed into downstream buckets.

## Data Layout and Naming
- Bucket split: CSV only in `raw/`; Parquet only in `conformed/` and `curated/`.
- Prefix convention for tabular data (per dataset): `raw/tabular/<dataset_id>/ingest_date=YYYY-MM-DD/<file>.csv`, mirroring into `conformed/tabular/<dataset_id>/.../*.parquet` and `curated/tabular/<dataset_id>/.../*.parquet`.
- Heartbeat isolated under `*/heartbeat/` to keep copy DAGs scoped.
- Object keys map 1:1 across stages (same base name, extension change); conversions are idempotent by key.
- Bucket data persists in Docker volumes (`minio-data`); `docker compose down -v` clears all objects.

## OHLCV Schema Decisions (yFinance ASX)
- Business key: `(dataset_id, company_identifier, trade_date)` for daily bars (or market_datetime if using intraday).
- Domain columns: `company_identifier`, `trade_date` (or market_datetime), `open`, `high`, `low`, `close`, `volume`, `exchange`, `currency` (optional: `adjusted_close`, `vwap`, `trade_count`).
- Ingestion/lineage columns added during conversion: `ingest_ts`, `ingest_batch_id`, `source_object_key`, `row_hash` (hash of logical row), optional `row_number_in_source`.
- Append-only in conformed: every raw CSV yields new Parquet objects; no in-place updates.
- Curated dedupe: latest-wins per business key based on `ingest_ts`, using `row_hash` to drop exact duplicates.

## Operational Notes
- Typical clean run sequence (PowerShell): `docker compose down -v`; remove custom Airflow image; `docker compose build airflow`; ensure `dags,logs,plugins` folders; `docker compose up -d`; verify with `docker ps` and `airflow users list`.
- Airflow admin user creation is made deterministic via the init service to avoid startup race/lock issues inside the main container.
- Airflow runtime: SequentialExecutor + SQLite (simple local dev); custom image installs `yfinance`, `pyarrow`, `pandas`.
- Health: webserver on 8080, MinIO console on 9001; container health depends on webserver `/health`.
- Change scope for future datasets: add new `<dataset_id>` prefixes under `tabular/` and reuse the scan-and-convert pattern.

## Components (configuration highlights)
- **docker-compose.yaml**: MinIO + bucket init; Airflow (custom image) with mounted `dags/logs/plugins`; user-init one-shot to create admin; host ports 8080/9000/9001 exposed.
- **Dockerfile**: extends `apache/airflow:2.10.3`, installs `yfinance`, `pyarrow`, `pandas` under `airflow` user.
- **Environment defaults**: `S3_ENDPOINT_URL=http://minio:9000`, `AWS_ACCESS_KEY_ID=AWS_SECRET_ACCESS_KEY=minioadmin`, `AIRFLOW_UID=50000` (harmless on Windows, useful on Linux/WSL).
- **Volumes**: `minio-data` (bucket objects) and `airflow-db` (SQLite metadata and dags/plugins/logs bind mounts).

## Layer Responsibilities
- **raw**: landing zone; only CSV (plus heartbeat .txt). Producer-specific naming under `tabular/<dataset_id>/...`. No dedupe, no type enforcement.
- **conformed**: typed Parquet; append-only; adds lineage columns; key mapping keeps path parity with raw but uses `.parquet`; no in-place updates.
- **curated**: analytics-ready; may overwrite per-partition snapshot; dedupe/latest-wins applied here; heartbeat copies land under `curated/heartbeat/`.

## Pipeline Construction Options (decisions taken)
- Change detection: chosen scheduled scans (list + compare) per prefix; alternatives (not yet used) include bucket notifications or Airflow Datasets.
- Conversion placement: chosen in-DAG conversion (PyArrow) inside Airflow container; alternative would be offloaded conversion container.
- Publish model: chosen physical copy/snapshot into curated; alternative logical view/manifest deferred.
- Dedupe strategy: conformed append-only; curated resolves duplicates via business key + `ingest_ts`/`row_hash`.

## Key Run Sequences (PowerShell)
- Clean reset: `docker compose down -v`; `docker image rm apache/airflow:2.10.3-custom 2>$null`; `Remove-Item -Recurse -Force .\logs 2>$null`.
- Prepare and build: `New-Item -ItemType Directory -Force -Path dags,logs,plugins | Out-Null`; `docker compose build airflow`.
- Start stack: `docker compose up -d`; check `docker ps --format '{{.Names}}: {{.Status}}' | sort`.
- Validate Airflow user: `docker exec -it airflow airflow users list`.
- List buckets: `docker compose exec -T minio mc ls local`; tail objects: `mc ls -r local/raw|conformed|curated | head`.
