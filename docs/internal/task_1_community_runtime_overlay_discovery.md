# Task 1 — Community Runtime and Overlay Discovery

## 1. Scope

This report covers repository evidence discovered in the Community repository on branch `feature/rearchitecture-runtime-overlay-contract`.

Read-only governing inputs used:

- `docs/architecture/overlay_contract_v1.md`
- `docs/internal/rearchitecture_task_tracker.md`
- `README.md`
- `RUNBOOK.md`
- `docs/reference/IMPLEMENTED_CAPABILITIES.md`

Runtime and configuration files were inspected but not modified. No Docker Compose commands were executed.

## 2. Repository State

| Item | Observation |
| --- | --- |
| Repository | `open-source-data-lake-community` |
| Working directory | `/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community` |
| Branch | `feature/rearchitecture-runtime-overlay-contract` |
| Baseline tag | `v1.0.0` exists in `.git/refs/tags/v1.0.0`; not modified |
| Initial `git status --short` | `?? docs/architecture/master_prompt.md`, `?? docs/internal/rearchitecture_task_tracker.md` |
| Runtime scope found | Base Compose runtime, overlay source trees, overlay packaged runtime folders, overlay zip archives, PHP UI, Airflow DAGs, notebooks, config, data, logs, plugins |

Repository-state observations relevant to the contract:

- The base runtime is Docker Compose based.
- The authoritative contract requires `airflow-webserver` and `airflow-scheduler` plus PostgreSQL metadata.
- The observed base runtime instead defines one logical `airflow` service with SQLite metadata.

## 3. Docker Compose Entry Points

| Path | Inferred purpose | Classification | Services started or referenced | Environment files referenced | Volumes / mounts | Networks | Image build references | Credentials / placeholders |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `docker-compose.yaml` | Base Community runtime | Primary entry point | `minio`, `minio-init`, `airflow`, `jupyter`, `php` | Compose auto-loads repo-root `.env` if present; defaults embedded with `${VAR:-default}` | Named volumes `minio-data`, `airflow-db`; bind mounts for `dags`, `logs`, `plugins`, `scripts`, `config`, `data`, `notebooks`, `php` | No explicit network definitions; default Compose network implied | `docker/airflow/Dockerfile`, `docker/jupyter/Dockerfile`; `minio/minio:latest`, `minio/mc:latest`, `dunglas/frankenphp:latest` | Multiple insecure defaults in file: `minioadmin`, `jupyter`, `admin@example.com` |
| `start-compose.sh` | Root wrapper that resolves `--overlay` files, validates Docker, then runs `docker compose build` and `up -d` | Primary entry point | Base services plus any overlay Compose layers passed with `--overlay` | Warns if `.env` absent; relies on repo-root `.env` and Compose defaults | Delegates to `docker-compose.yaml` and overlay files only | None explicit | Builds all selected Compose services | None embedded; may pass through values from `.env` |
| `stop-compose.sh` | Root wrapper that resolves `--overlay` files and runs `docker compose down` or `down -v` | Primary entry point | Base services plus any overlay Compose layers passed with `--overlay` | Indirect only | Delegates to selected Compose files | None explicit | None | None |
| `overlay_hello_world/dev-docker-compose.overlay-hello-world.yaml` | Source-tree development overlay for hello-world | Overlay Compose file | Overrides `airflow`, `jupyter`, `php` only | Uses repo-root `.env`; default `ENABLED_SOLUTION_TAGS=hello-world` | Overlay-specific DAG, notebook, script, config, sample-data, PHP solution mounts | No explicit network definitions | `overlay_hello_world/overlay_hello_world/docker/airflow/Dockerfile`, `.../docker/jupyter/Dockerfile` | Placeholder-style defaults only |
| `overlay_hello_world/overlay_hello_world/docker-compose.overlay-hello-world.yaml` | Packaged overlay Compose file for installed hello-world overlay | Overlay Compose file | Overrides `airflow`, `jupyter`, `php` only | Uses repo-root `.env`; default `ENABLED_SOLUTION_TAGS=hello-world` | No volumes in packaged file; assumes overlay payload already unzipped into runtime surface | No explicit network definitions | `overlay_hello_world/docker/airflow/Dockerfile`, `.../docker/jupyter/Dockerfile` | Placeholder-style defaults only |
| `overlay_hello_world/dev-start-compose.sh` | Source-tree helper wrapper | Helper script | Calls root `start-compose.sh --overlay overlay_hello_world/dev-docker-compose.overlay-hello-world.yaml` | Repo-root `.env` via root wrapper | None directly | None | None directly | None |
| `overlay_hello_world/dev-stop-compose.sh` | Source-tree helper wrapper | Helper script | Calls root `stop-compose.sh --overlay overlay_hello_world/dev-docker-compose.overlay-hello-world.yaml` | Repo-root `.env` via root wrapper | None directly | None | None directly | None |
| `overlay_hello_world/overlay_hello_world/start-compose.sh` | Packaged helper wrapper | Helper script | Calls root `start-compose.sh --overlay overlay_hello_world/docker-compose.overlay-hello-world.yaml` | Repo-root `.env` via root wrapper | None directly | None | None directly | None |
| `overlay_hello_world/overlay_hello_world/stop-compose.sh` | Packaged helper wrapper | Helper script | Calls root `stop-compose.sh --overlay overlay_hello_world/docker-compose.overlay-hello-world.yaml` | Repo-root `.env` via root wrapper | None directly | None | None directly | None |
| `overlay_heartbeat_v2/dev-docker-compose.overlay-heartbeat-v2.yaml` | Source-tree development overlay that mounts additive DAGs and notebooks only | Overlay Compose file | Overrides `airflow`, `jupyter` only | No overlay env file referenced | Read-only mounts from `overlay_heartbeat_v2/dags` and `overlay_heartbeat_v2/notebooks` | No explicit network definitions | No new image builds | No credentials present |
| `overlay_heartbeat_v2/dev-start-compose.sh` | Source-tree helper wrapper | Helper script | Calls root `start-compose.sh --overlay overlay_heartbeat_v2/dev-docker-compose.overlay-heartbeat-v2.yaml` | Repo-root `.env` via root wrapper | None directly | None | None directly | None |
| `overlay_heartbeat_v2/dev-stop-compose.sh` | Source-tree helper wrapper | Helper script | Calls root `stop-compose.sh --overlay overlay_heartbeat_v2/dev-docker-compose.overlay-heartbeat-v2.yaml` | Repo-root `.env` via root wrapper | None directly | None | None directly | None |
| `overlay_heartbeat_v2/overlay_heartbeat_v2/start-compose.sh` | Packaged helper wrapper for zip-installed heartbeat overlay | Helper script | Calls root `start-compose.sh` with no `--overlay` | Repo-root `.env` via root wrapper | None directly | None | None directly | None |
| `overlay_heartbeat_v2/overlay_heartbeat_v2/stop-compose.sh` | Packaged helper wrapper for zip-installed heartbeat overlay | Helper script | Calls root `stop-compose.sh` with no `--overlay` | Repo-root `.env` via root wrapper | None directly | None | None directly | None |
| `overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml` | Source-tree development overlay for ASX historic ingestion | Overlay Compose file | Overrides `airflow`, `jupyter`, `php` only | Uses repo-root `.env`; outer `overlay_asx_historic_csv/.env.example` is documentation/template only | Additional `scripts`, `data`, `config` binds for overlay workflow and PHP summary access | No explicit network definitions | `overlay_asx_historic_csv/overlay_asx_historic_csv/docker/airflow/Dockerfile`, `.../docker/jupyter/Dockerfile` | Placeholder defaults for MinIO/Jupyter in outer `.env.example` |
| `overlay_asx_historic_csv/overlay_asx_historic_csv/docker-compose.overlay-asx-historic-csv.yaml` | Packaged overlay Compose file | Overlay Compose file | Overrides `airflow`, `jupyter`, `php` only | Uses repo-root `.env`; packaged README instructs copying example JSON into `config/asx_historic_jobs.json` | Additional `scripts`, `data`, `config` binds | No explicit network definitions | `overlay_asx_historic_csv/docker/airflow/Dockerfile`, `.../docker/jupyter/Dockerfile` | Placeholder defaults only |
| `overlay_asx_historic_csv/dev-start-compose.sh` | Source-tree helper wrapper | Helper script | Calls root `start-compose.sh --overlay overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml` | Repo-root `.env` via root wrapper | None directly | None | None directly | None |
| `overlay_asx_historic_csv/dev-stop-compose.sh` | Source-tree helper wrapper | Helper script | Calls root `stop-compose.sh --overlay overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml` | Repo-root `.env` via root wrapper | None directly | None | None directly | None |
| `overlay_asx_historic_csv/overlay_asx_historic_csv/start-compose.sh` | Packaged helper wrapper | Helper script | Calls root `start-compose.sh --overlay overlay_asx_historic_csv/docker-compose.overlay-asx-historic-csv.yaml` | Repo-root `.env` via root wrapper | None directly | None | None directly | None |
| `overlay_asx_historic_csv/overlay_asx_historic_csv/stop-compose.sh` | Packaged helper wrapper | Helper script | Calls root `stop-compose.sh --overlay overlay_asx_historic_csv/docker-compose.overlay-asx-historic-csv.yaml` | Repo-root `.env` via root wrapper | None directly | None | None directly | None |
| `overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml` | Source-tree development overlay for Kaggle ingestion | Overlay Compose file | Overrides `airflow`, `jupyter`, `php` only | Uses repo-root `.env`; outer `overlay_kaggle_ingestion/.env.example` is documentation/template only | Additional `scripts`, `data`, `config` binds | No explicit network definitions | `overlay_kaggle_ingestion/overlay_kaggle_ingestion/docker/airflow/Dockerfile`, `.../docker/jupyter/Dockerfile` | Placeholder values in template; runtime file references Kaggle credentials |
| `overlay_kaggle_ingestion/overlay_kaggle_ingestion/docker-compose.overlay-kaggle.yaml` | Packaged overlay Compose file | Overlay Compose file | Overrides `airflow`, `jupyter`, `php` only | Uses repo-root `.env`; packaged README instructs configuring Kaggle credentials in `.env` or shell | Additional `scripts`, `data`, `config` binds | No explicit network definitions | `overlay_kaggle_ingestion/docker/airflow/Dockerfile`, `.../docker/jupyter/Dockerfile` | Placeholder defaults in compose, but actual credentials were found in repo-root `.env` |
| `overlay_kaggle_ingestion/dev-start-compose.sh` | Source-tree helper wrapper | Helper script | Calls root `start-compose.sh --overlay overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml` | Repo-root `.env` via root wrapper | None directly | None | None directly | None |
| `overlay_kaggle_ingestion/dev-stop-compose.sh` | Source-tree helper wrapper | Helper script | Calls root `stop-compose.sh --overlay overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml` | Repo-root `.env` via root wrapper | None directly | None | None directly | None |
| `overlay_kaggle_ingestion/overlay_kaggle_ingestion/start-compose.sh` | Packaged helper wrapper | Helper script | Calls root `start-compose.sh --overlay overlay_kaggle_ingestion/docker-compose.overlay-kaggle.yaml` | Repo-root `.env` via root wrapper | None directly | None | None directly | None |
| `overlay_kaggle_ingestion/overlay_kaggle_ingestion/stop-compose.sh` | Packaged helper wrapper | Helper script | Calls root `stop-compose.sh --overlay overlay_kaggle_ingestion/docker-compose.overlay-kaggle.yaml` | Repo-root `.env` via root wrapper | None directly | None | None directly | None |

## 4. Runtime Structure

### Runtime-relevant directories observed

| Path | Relevance |
| --- | --- |
| `config/` | Base runtime operator config; `asx200_tickers.csv` expected locally but not committed |
| `dags/` | Base Airflow DAG surface |
| `data/` | Runtime output surface; includes `raw/`, `conformed/`, `curated/` |
| `docker/airflow`, `docker/jupyter` | Base custom image definitions |
| `docs/` | Governance, architecture, and reference docs |
| `logs/` | Runtime logs; contract says `logs/` is non-contract |
| `notebooks/` | Base notebook surface |
| `php/` | Base UI surface including service index, health page, and solution discovery |
| `plugins/` | Mounted into Airflow; contract says `plugins/` is non-contract |
| `scripts/` | Base shared runtime code surface |
| `overlay_hello_world/`, `overlay_asx_historic_csv/`, `overlay_kaggle_ingestion/`, `overlay_heartbeat_v2/`, `overlay_file_only_demo/` | Overlay source trees and packaged-runtime folders |
| `overlay_contract/` | Non-authoritative contract/reference material inside the repo |

### Notable absences

| Expected category from task | Observation |
| --- | --- |
| `kubernetes/` runtime tree | Not present |
| `helm/` runtime tree | Not present |
| `minio/` dedicated config directory | Not present; MinIO is defined only in Compose |
| `trino/` runtime directory | Not present |
| External database config directory | Not present; Airflow metadata is configured inline in Compose as SQLite |
| Separate `airflow-webserver` / `airflow-scheduler` service directories | Not present |

### Other runtime evidence

- `data/raw`, `data/conformed`, and `data/curated` exist and align with the contract data zones.
- `logs/` contains historical Airflow execution logs for base DAGs and overlay DAGs, including `dag_asx_historic_csv`, `dag_kaggle_ingestion`, and `heartbeat_v2_*`.
- `dags/overlay_heartbeat_v2/` and `notebooks/overlay_heartbeat_v2/` exist as directories but contained no files at inspection time.

## 5. Service Definitions

| Service name | Source file path | Image / build context | Exposed ports | Volumes | Environment variables observed | Dependencies | Health check | Classification | Runtime type |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `minio` | `docker-compose.yaml` | `minio/minio:latest` | `${MINIO_API_PORT:-9000}:9000`, `${MINIO_CONSOLE_PORT:-9001}:9001` | `minio-data:/data` | `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` | None | `curl -f http://localhost:9000/minio/health/live` | Required | Compose |
| `minio-init` | `docker-compose.yaml` | `minio/mc:latest` | None | None | Uses `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` inside entrypoint | Depends on healthy `minio` | None | Required helper job | Compose |
| `airflow` | `docker-compose.yaml` | Build `docker/airflow/Dockerfile`; image tag `apache/airflow:2.10.3-custom` | `${AIRFLOW_PORT:-8080}:8080` | `./dags`, `./logs`, `./plugins`, `./scripts`, `./config:ro`, `./data`, `airflow-db:/opt/airflow` | `AIRFLOW__CORE__EXECUTOR`, `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN`, `AIRFLOW__CORE__LOAD_EXAMPLES`, `AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION`, `AIRFLOW__WEBSERVER__EXPOSE_CONFIG`, `S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`, `AIRFLOW_UID`, `PIP_ADDITIONAL_REQUIREMENTS`, `AIRFLOW_VAR_ASX_TICKERS`, `AIRFLOW_ADMIN_USERNAME`, `AIRFLOW_ADMIN_PASSWORD`, `AIRFLOW_ADMIN_EMAIL` | Depends on `minio` healthy and `minio-init` completed | `curl -fsS http://localhost:8080/health` | Required, but contract-noncompliant as a logical wrapper | Compose |
| `jupyter` | `docker-compose.yaml` | Build `docker/jupyter/Dockerfile`; image tag `jupyter/minimal-notebook:custom` | `${JUPYTER_PORT:-8888}:8888` | `./notebooks`, `./config:ro`, `./data` | `JUPYTER_TOKEN` | None | None | Optional | Compose |
| `php` | `docker-compose.yaml` | `dunglas/frankenphp:latest` | `${PHP_PORT:-8088}:80` | `./php:/app/public`, `./data:/app/data:ro` | `SERVER_NAME`, `TZ` | None | None | Optional | Compose |
| `airflow` overlay override | `overlay_hello_world/dev-docker-compose.overlay-hello-world.yaml` and packaged variant | Build overlay-specific Dockerfile; image `apache/airflow:2.10.3-hello-world` | None new | Overlay DAG, script, config, sample-data mounts in dev file | `HELLO_WORLD_CONFIG_DIR`, `HELLO_WORLD_LOCAL_DATA_DIR`, `HELLO_WORLD_SAMPLE_DIR` | Inherits base service dependency graph | Inherits base health check | Optional overlay extension | Compose |
| `jupyter` overlay override | `overlay_hello_world/dev-docker-compose.overlay-hello-world.yaml` and packaged variant | Build overlay-specific Dockerfile; image `jupyter/minimal-notebook:hello-world` | None new | Overlay notebook, script, config, sample-data mounts in dev file | `HELLO_WORLD_CONFIG_DIR`, `HELLO_WORLD_LOCAL_DATA_DIR`, `HELLO_WORLD_SAMPLE_DIR` | None explicit | None | Optional overlay extension | Compose |
| `php` overlay override | `overlay_hello_world/dev-docker-compose.overlay-hello-world.yaml` and packaged variant | Inherits base image | None new | `./overlay_hello_world/php/solutions:/app/public/solutions` in dev file | `ENABLED_SOLUTION_TAGS` | None | None | Optional overlay extension | Compose |
| `airflow` overlay override | `overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml` and packaged variant | Build overlay-specific Dockerfile | None new | `./scripts`, `./data` | No new env vars added in compose | Inherits base dependency graph | Inherits base health check | Optional overlay extension | Compose |
| `jupyter` overlay override | `overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml` and packaged variant | Build overlay-specific Dockerfile | None new | `./config:ro`, `./scripts:ro`, `./data` | `S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION` | None explicit | None | Optional overlay extension | Compose |
| `php` overlay override | `overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml` and packaged variant | Inherits base image | None new | `./data:/app/data:ro` | `ENABLED_SOLUTION_TAGS=asx-historic-csv` | None | None | Optional overlay extension | Compose |
| `airflow` overlay override | `overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml` and packaged variant | Build overlay-specific Dockerfile | None new | `./scripts`, `./data` | `KAGGLE_API_TOKEN`, `KAGGLE_USERNAME`, `KAGGLE_KEY`, `KAGGLE_CONFIG_DIR` | Inherits base dependency graph | Inherits base health check | Optional overlay extension | Compose |
| `jupyter` overlay override | `overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml` and packaged variant | Build overlay-specific Dockerfile | None new | `./config:ro`, `./scripts:ro`, `./data` | `KAGGLE_API_TOKEN`, `KAGGLE_USERNAME`, `KAGGLE_KEY`, `KAGGLE_CONFIG_DIR`, `S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION` | None explicit | None | Optional overlay extension | Compose |
| `php` overlay override | `overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml` and packaged variant | Inherits base image | None new | `./data:/app/data:ro` | `ENABLED_SOLUTION_TAGS=kaggle` | None | None | Optional overlay extension | Compose |
| `airflow` overlay override | `overlay_heartbeat_v2/dev-docker-compose.overlay-heartbeat-v2.yaml` | Inherits base image/build | None new | `./overlay_heartbeat_v2/dags:/opt/airflow/dags/overlay_heartbeat_v2:ro` | None added | Inherits base dependency graph | Inherits base health check | Optional overlay extension | Compose |
| `jupyter` overlay override | `overlay_heartbeat_v2/dev-docker-compose.overlay-heartbeat-v2.yaml` | Inherits base image/build | None new | `./overlay_heartbeat_v2/notebooks:/home/jovyan/work/overlay_heartbeat_v2:ro` | None added | None explicit | None | Optional overlay extension | Compose |

Additional service-related observations:

- The PHP UI hard-codes external home-page links for Airflow, Jupyter, MinIO Console, MinIO API, and exposes an internal health-check page that probes `airflow`, `jupyter`, and `minio` container DNS names.
- No overlay Compose file adds a new top-level service name. All observed overlays mutate existing base services only.

## 6. Environment Configuration

### Environment files present

| Path | Purpose | Notes |
| --- | --- | --- |
| `.env.example` | Base template for local overrides | Contains placeholder/default values only |
| `.env` | Active repo-root environment file | Contains real Kaggle credentials; see Secrets Contract Assessment |
| `overlay_hello_world/overlay_hello_world/.env.example` | Packaged hello-world template | Contains `ENABLED_SOLUTION_TAGS=hello-world` |
| `overlay_asx_historic_csv/.env.example` | Outer/source-tree ASX historic template | Placeholder/default values for MinIO, Jupyter, and ASX bucket names |
| `overlay_kaggle_ingestion/.env.example` | Outer/source-tree Kaggle template | Placeholder/default values plus Kaggle placeholder credential fields |

### Environment references observed in Compose and scripts

| Variable group | Referenced by | Default or source observed | Notes |
| --- | --- | --- | --- |
| `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_API_PORT`, `MINIO_CONSOLE_PORT` | Base Compose, overlay Compose, notebooks, scripts | Defaults in `docker-compose.yaml` and `.env.example` | Also reused as AWS-compatible access keys for MinIO |
| `AIRFLOW_PORT`, `AIRFLOW_UID`, `AIRFLOW_ADMIN_USERNAME`, `AIRFLOW_ADMIN_PASSWORD`, `AIRFLOW_ADMIN_EMAIL`, `AIRFLOW_PIP_ADDITIONAL_REQUIREMENTS`, `AIRFLOW_VAR_ASX_TICKERS` | Base Compose | Defaults in `docker-compose.yaml` and `.env.example` | Admin defaults are insecure placeholders |
| `JUPYTER_PORT`, `JUPYTER_TOKEN` | Base Compose, `.env.example` | Defaults in `docker-compose.yaml` and `.env.example` | Token default is fixed string `jupyter` |
| `PHP_PORT`, `TZ` | Base Compose | Defaults in `docker-compose.yaml` and `.env.example` | `TZ` default `Australia/Melbourne` |
| `ENABLED_SOLUTION_TAGS` | Hello-world overlay Compose, `php/solutions.php` | Default `hello-world` in hello-world overlay; fixed values in other overlay Compose files | Controls which solution pages appear in PHP UI |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`, `S3_ENDPOINT_URL` | Base Airflow service, overlay Jupyter services, DAGs, overlay scripts | Compose sets MinIO-derived defaults; scripts also fall back to `minioadmin` and `us-east-1` | Shared storage access contract across runtime and overlays |
| `HELLO_WORLD_CONFIG_DIR`, `HELLO_WORLD_LOCAL_DATA_DIR`, `HELLO_WORLD_SAMPLE_DIR` | Hello-world overlay Compose and scripts | Set only by hello-world overlay Compose | Overlay-specific |
| `KAGGLE_API_TOKEN`, `KAGGLE_USERNAME`, `KAGGLE_KEY`, `KAGGLE_CONFIG_DIR` | Kaggle overlay Compose, scripts, notebooks, README | Compose defaults empty; `.env.example` uses placeholders; repo-root `.env` contains real values | Overlay-specific secret-bearing variables |
| `KAGGLE_RAW_BUCKET`, `KAGGLE_CONFORMED_BUCKET`, `KAGGLE_CURATED_BUCKET` | Kaggle overlay scripts and notebooks | Script defaults `raw`, `conformed`, `curated` | Overlay-specific, not declared in Compose |
| `KAGGLE_JOBS_CONFIG`, `KAGGLE_JOB_NAME`, `KAGGLE_CURATED_SUMMARY_PATH`, `OPEN_DATA_LAKE_REPO_ROOT` | Kaggle overlay DAG / PHP | Script/DAG fallback defaults in code | Overlay-specific, not declared in Compose |
| `ASX_RAW_BUCKET`, `ASX_CONFORMED_BUCKET`, `ASX_CURATED_BUCKET`, `ASX_CURATED_LOCAL_ROOT` | ASX overlay scripts and notebooks | Script defaults `raw`, `conformed`, `curated`; local-root fallback in code | Overlay-specific, not declared in Compose |
| `ASX_HISTORIC_JOB_NAME` | ASX historic DAG | No Compose declaration; code reads env if provided | Overlay-specific |

### Config and state files relevant to runtime

| Path | Observed role | Contract note |
| --- | --- | --- |
| `config/asx200_tickers.csv` | Expected local operator file; not committed | Mutable operator config outside Git-tracked baseline |
| `overlay_hello_world/config/hello_world_job.example.json` | Example overlay config/state payload | Placeholder/example only |
| `overlay_asx_historic_csv/config/asx_historic_jobs.example.json` | Example overlay config/state payload | Placeholder/example only |
| `overlay_kaggle_ingestion/config/kaggle_jobs.example.json` | Example overlay config/state payload | Placeholder/example only |
| `config/asx200_tickers_top3.csv`, `config/asx200_tickers_top100.csv` | Sample ticker inputs | Example only |

### Secrets Contract Assessment

| Location | Assessment | Evidence |
| --- | --- | --- |
| `.env.example` | Acceptable placeholder/default file | Contains defaults and examples only |
| `overlay_asx_historic_csv/.env.example` | Acceptable placeholder/default file | Contains example MinIO/Jupyter/bucket settings only |
| `overlay_kaggle_ingestion/.env.example` | Acceptable placeholder/default file | Uses placeholder strings such as `your_kaggle_api_token` |
| `overlay_hello_world/overlay_hello_world/.env.example` | Acceptable non-secret toggle file | Contains only `ENABLED_SOLUTION_TAGS=hello-world` |
| `.env` | Contract violation | Contains non-placeholder Kaggle credential values for `KAGGLE_API_TOKEN`, `KAGGLE_USERNAME`, and `KAGGLE_KEY`; values redacted as `[REDACTED]` |

Additional secrets observations:

- Base Compose defaults expose weak demo credentials such as `minioadmin` and `jupyter`. These are placeholders/insecure defaults, not unique real secrets.
- The authoritative contract forbids real credentials in overlays. The real credential leak was found in repo-root `.env`, not in the overlay example files themselves.

## 7. Overlay Discovery

| Path | Why it appears to be an overlay or variant | Type | Alignment with `overlay_contract_v1.md` | Status |
| --- | --- | --- | --- | --- |
| `overlay_hello_world/` | Full overlay source tree with `config`, `dags`, `notebooks`, `scripts`, `data`, `php`, packaged runtime folder, dev overlay Compose file, zip archive | Compose | Strong alignment: matches standard folders and optional overlay Compose activation | Active |
| `overlay_hello_world/overlay_hello_world/` | Packaged runtime folder meant to be unzipped into installation root and activated via overlay wrapper | Compose | Strong alignment | Active |
| `overlay_hello_world/dev-docker-compose.overlay-hello-world.yaml` | Source-tree overlay activation file | Compose | Strong alignment; uses service overrides only | Active |
| `overlay_heartbeat_v2/` | Additive overlay source tree with DAGs, notebooks, dev overlay Compose, zip archive, packaged docs | Compose / file-only hybrid | Partial alignment: filesystem overlay aligns; packaged runtime does not use overlay Compose at start time because payload is expected to land in base mount surfaces | Active |
| `overlay_heartbeat_v2/overlay_heartbeat_v2/` | Packaged runtime folder with wrapper docs/scripts only | Config-only / docs-only packaging helper | Partial alignment: wrapper delegates to base start/stop without `--overlay`; valid only because packaged payload is copied into base contract folders | Active but packaging-specific |
| `overlay_heartbeat_v2/dev-docker-compose.overlay-heartbeat-v2.yaml` | Source-tree overlay mount file | Compose | Strong alignment for development activation | Active |
| `overlay_asx_historic_csv/` | Full overlay source tree with packaged runtime folder, config, scripts, DAG, notebooks, PHP solution, dev overlay Compose, zip archive | Compose | Strong alignment | Active |
| `overlay_asx_historic_csv/overlay_asx_historic_csv/` | Packaged runtime folder for installed overlay | Compose | Strong alignment | Active |
| `overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml` | Source-tree overlay activation file | Compose | Strong alignment | Active |
| `overlay_kaggle_ingestion/` | Full overlay source tree with packaged runtime folder, config, scripts, DAG, notebooks, PHP solution, dev overlay Compose, zip archive | Compose | Strong alignment structurally; secrets handling depends on external env discipline | Active |
| `overlay_kaggle_ingestion/overlay_kaggle_ingestion/` | Packaged runtime folder for installed overlay | Compose | Strong alignment structurally | Active |
| `overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml` | Source-tree overlay activation file | Compose | Strong alignment; overlays env/service overrides only | Active |
| `overlay_file_only_demo/` | Minimal overlay example with packaged docs and PHP solution only | Config-only / docs-only / file-only | Aligns with contract because all standard folders are optional and overlay YAML is optional | Active example |
| `overlay_file_only_demo/overlay_file_only_demo/` | Packaged file-only runtime folder | Docs-only packaging helper | Aligns with contract | Active example |
| `overlay_contract/` | Internal overlay-authoring contract/reference material | Docs-only | Not authoritative for this task; overlaps with but is different from `docs/architecture/overlay_contract_v1.md` | Active docs, authority ambiguous |
| `docs/internal/discovery_overlay_heartbeat_v2.md` and `docs/internal/validation_overlay_heartbeat_v2.md` | Overlay-specific analysis documents | Docs-only | Supplemental only | Active docs |
| `.git/refs/heads/feature/k8s-rebuild-from-compose` and matching git-log refs | Contains `k8s` search match | Kubernetes-related git metadata, not runtime overlay | Not part of runtime contract surface | Stale/non-runtime evidence |

Overlay discovery summary:

- No Kubernetes runtime overlays or Helm runtime charts were present in repository working files.
- All operational overlay artifacts observed are Docker Compose overlays or file-only overlays.
- Overlay zip archives exist for `overlay_hello_world`, `overlay_heartbeat_v2`, `overlay_asx_historic_csv`, `overlay_kaggle_ingestion`, and `overlay_file_only_demo`.

## 8. Airflow Contract Assessment

| Contract item | Observed evidence | Assessment |
| --- | --- | --- |
| `airflow-webserver` must exist | Base Compose defines only `airflow` | Not satisfied |
| `airflow-scheduler` must exist | Base Compose defines only `airflow` | Not satisfied |
| No logical airflow wrapper service should be treated as compliant | The single service is explicitly a combined webserver/scheduler command: `airflow webserver & airflow scheduler` | Not satisfied |
| Metadata database must be PostgreSQL | Base Compose sets `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: sqlite:////opt/airflow/airflow.db`; README and runbook also describe SQLite | Not satisfied |
| Overlay interaction should occur through filesystem surfaces | Overlays add DAGs, scripts, config, notebooks, PHP pages, and limited service overrides | Satisfied structurally |

Airflow conclusion:

- The current Community runtime does not satisfy the authoritative Airflow service contract.
- Overlay authoring in the repo assumes the base `airflow` service exists and mounts standard folders, so overlays are built against the current combined-service runtime rather than the authoritative target runtime.

## 9. Dependency Contract Assessment

### Base images and custom images

| Image or Dockerfile | Base image | Added dependencies observed |
| --- | --- | --- |
| `docker/airflow/Dockerfile` | `apache/airflow:2.10.3` | `yfinance`, `pyarrow`, `pandas`, `openpyxl`, `xlrd` |
| `docker/jupyter/Dockerfile` | `jupyter/minimal-notebook:latest` | `pandas`, `pyarrow`, `matplotlib`, `minio`, `duckdb`, `openpyxl`, `xlrd` |
| `overlay_hello_world/overlay_hello_world/docker/airflow/Dockerfile` | `apache/airflow:2.10.3` | `boto3`, `pandas`, `pyarrow`, `yfinance` |
| `overlay_hello_world/overlay_hello_world/docker/jupyter/Dockerfile` | `jupyter/minimal-notebook:latest` | `boto3`, `duckdb`, `matplotlib`, `minio`, `pandas`, `pyarrow` |
| `overlay_asx_historic_csv/overlay_asx_historic_csv/docker/airflow/Dockerfile` | `apache/airflow:2.10.3` | `yfinance`, `pyarrow`, `pandas`, `openpyxl`, `xlrd` |
| `overlay_asx_historic_csv/overlay_asx_historic_csv/docker/jupyter/Dockerfile` | `jupyter/minimal-notebook:latest` | `pandas`, `pyarrow`, `matplotlib`, `minio`, `duckdb`, `openpyxl`, `xlrd` |
| `overlay_kaggle_ingestion/overlay_kaggle_ingestion/docker/airflow/Dockerfile` | `apache/airflow:2.10.3` | `boto3`, `kaggle`, `pandas`, `pyarrow`, `yfinance` |
| `overlay_kaggle_ingestion/overlay_kaggle_ingestion/docker/jupyter/Dockerfile` | `jupyter/minimal-notebook:latest` | `kaggle`, `matplotlib`, `minio`, `duckdb`, `pandas`, `pyarrow` |

### Assessment

| Area | Observation | Assessment |
| --- | --- | --- |
| Shared dependencies in base runtime | Base Airflow and Jupyter images explicitly add common data dependencies | Aligned with contract intent |
| Overlay-specific dependencies | Hello-world explicitly adds `boto3`; Kaggle explicitly adds `kaggle`; ASX historic explicitly adds spreadsheet readers in overlay images | Aligned where declared |
| Implicit inheritance risks | Base Compose also injects `PIP_ADDITIONAL_REQUIREMENTS` at runtime for Airflow, duplicating packages already baked into `docker/airflow/Dockerfile` | Risk: mixed image-baked vs runtime-installed dependency model |
| Overlay dependency inheritance | Overlay Compose files replace image builds for `airflow` and `jupyter` rather than extending base custom tags, so overlays may bypass base custom image assumptions unless their Dockerfiles reproduce needed packages | Risk present |
| Missing explicit dependency declarations | Several overlay scripts and DAGs use env vars not declared in Compose, for example `KAGGLE_JOBS_CONFIG`, `KAGGLE_JOB_NAME`, `ASX_HISTORIC_JOB_NAME`, `ASX_CURATED_LOCAL_ROOT`, `KAGGLE_CURATED_SUMMARY_PATH`, `OPEN_DATA_LAKE_REPO_ROOT` | Risk present |
| Storage client assumptions | Multiple DAGs and overlay scripts fall back to hard-coded MinIO endpoint and default access keys | Risk: implicit runtime assumptions instead of explicit environment contract |

Dependency conclusion:

- The repository mostly declares Python dependencies explicitly through Dockerfiles.
- The dependency model is not fully clean because the base Airflow service mixes image-level packages with `PIP_ADDITIONAL_REQUIREMENTS`, and several overlays depend on undeclared-but-coded environment variables.

## 10. Risks, Ambiguities, and Questions

1. The authoritative Airflow contract and the implemented Community runtime do not match. The contract requires `airflow-webserver`, `airflow-scheduler`, and PostgreSQL, while the implementation uses one `airflow` service and SQLite.
2. Repo-root `.env` contains real Kaggle credentials `[REDACTED]`. This is the clearest secrets-governance issue found.
3. `overlay_contract/` documents a Compose overlay contract that is not the authoritative contract for this task. This creates documentation authority ambiguity inside the same repository.
4. `overlay_heartbeat_v2` is partly file-only and partly Compose-activated. Its dev flow uses an overlay Compose file, but its packaged flow starts without `--overlay`. That is workable for copied files, but it means overlay activation behavior differs between source-tree and packaged modes.
5. The base PHP UI and health page assume only the current base services. They do not discover services dynamically from overlay definitions.
6. `PIP_ADDITIONAL_REQUIREMENTS` duplicates package installation already present in `docker/airflow/Dockerfile`, which increases drift risk between documented and actual dependency state.
7. Overlay scripts rely on additional environment variables that are not surfaced in Compose files, so some overlay runtime behavior remains implicit.
8. `dags/overlay_heartbeat_v2/` and `notebooks/overlay_heartbeat_v2/` exist but were empty at inspection time, which may indicate leftover mount targets or incomplete packaging cleanup.

## 11. Recommended Next Task

Proceed to Task 2 in the tracker sequence, with priority on reconciling the implemented Community runtime against the authoritative contract before further overlay contract hardening.

The highest-value follow-on checks are:

- split the logical `airflow` service into contract-compliant `airflow-webserver` and `airflow-scheduler` definitions, or document why the authoritative contract must change
- replace SQLite metadata with PostgreSQL if the authoritative contract remains unchanged
- remove real secrets from repo-root `.env` and move them to a non-repository injection path
- standardize overlay activation so packaged and source-tree modes use the same contract where possible

## 12. Validation Evidence

Commands executed for discovery:

- `pwd`
- `git status --short`
- `git branch --show-current`
- `sed -n` reads of governing docs, Compose files, scripts, Dockerfiles, PHP files, and config examples
- `find . -maxdepth 4 -type f \( -name '*compose*.yml' -o -name '*compose*.yaml' -o -name 'docker-compose.yml' -o -name 'docker-compose.yaml' -o -name 'start*.sh' -o -name 'stop*.sh' \) | sort`
- `find . -maxdepth 3 -type d | sort`
- `find . -maxdepth 4 -type f | sort`
- `find . -maxdepth 5 -type f \( -name '.env*' -o -name '*env*' -o -name '*.properties' -o -name '*.conf' -o -name '*.ini' -o -name '*.yaml' -o -name '*.yml' \) | sort`
- `find . -maxdepth 6 \( -iname '*overlay*' -o -iname '*override*' -o -iname '*profile*' -o -iname '*variant*' -o -iname '*k8s*' -o -iname '*helm*' \)`
- `rg` scans for Dockerfiles, environment-variable references, and overlay/runtime evidence

Validation constraints and result:

| Check | Result |
| --- | --- |
| Repository path matched requested repository | Pass |
| Branch matched `feature/rearchitecture-runtime-overlay-contract` | Pass |
| No runtime/configuration files modified during Task 1 | Pass |
| `docs/architecture/master_prompt.md` treated as known supervisory documentation | Pass; it is not a runtime/configuration file and its presence does not indicate a forbidden runtime change |
| Allowed non-runtime documentation files present in `git status --short` | Pass; the only non-runtime changes/untracked files are `docs/internal/task_1_community_runtime_overlay_discovery.md`, `docs/internal/rearchitecture_task_tracker.md`, and `docs/architecture/master_prompt.md` |
| No Docker Compose runtime executed | Pass |
