# OV-05 — Community Dev-Mode Overlay Validation

## Branch Verification
- Branch: `feature/rearchitecture-runtime-overlay-contract`
- Result: pass

## Validation Summary Table

| overlay | dev_command | start_result | airflow | jupyter | php_ui | object_store | result | notes |
|---|---|---|---|---|---|---|---|---|
| `overlay_hello_world` | `bash overlay_hello_world/dev-start-compose.sh` | blocked | blocked | blocked | blocked | blocked | blocked | Root `start-compose.sh` rejected incomplete repo `.env`; runtime never started. |
| `overlay_heartbeat_v2` | `bash overlay_heartbeat_v2/dev-start-compose.sh` | blocked | blocked | blocked | blocked | blocked | blocked | Root `start-compose.sh` rejected incomplete repo `.env`; runtime never started. |
| `overlay_asx_historic_csv` | `bash overlay_asx_historic_csv/dev-start-compose.sh` | blocked | blocked | blocked | blocked | blocked | blocked | Root `start-compose.sh` rejected incomplete repo `.env`; runtime never started. |
| `overlay_kaggle_ingestion` | `bash overlay_kaggle_ingestion/dev-start-compose.sh` | blocked | blocked | blocked | blocked | blocked | blocked | Root `start-compose.sh` rejected incomplete repo `.env`; runtime never started. |
| `overlay_file_only_demo` | `./start-compose.sh` | blocked | blocked | blocked | blocked | blocked | blocked | Documented dev mode uses base stack only; base `start-compose.sh` rejected incomplete repo `.env`. |

## Detailed Results

### overlay_hello_world

#### Command
`bash overlay_hello_world/dev-start-compose.sh`

#### Start Result
blocked

#### Observations
- Runtime did not start.
- No containers were started for this overlay.
- Airflow, Jupyter, PHP UI, DAG visibility, and object-store checks were not reachable because the root runtime validation gate failed before `docker compose build` or `docker compose up -d`.

#### Result
blocked

#### Evidence
- Commands run:
  - `docker compose down`
  - `bash overlay_hello_world/dev-start-compose.sh`
- Key log excerpts:
  - `Resolved overlays (merge order):`
  - `- overlay_hello_world/dev-docker-compose.overlay-hello-world.yaml`
  - `Error: required Community env values are incomplete in /Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/.env`
  - `Missing required variables: AIRFLOW_POSTGRES_USER, AIRFLOW_POSTGRES_PASSWORD, AIRFLOW_POSTGRES_DB, AIRFLOW_ADMIN_USERNAME, AIRFLOW_ADMIN_PASSWORD, AIRFLOW_ADMIN_EMAIL, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD, JUPYTER_TOKEN, PHP_PORT, AIRFLOW_PORT, JUPYTER_PORT, MINIO_API_PORT, MINIO_CONSOLE_PORT, AWS_DEFAULT_REGION, AIRFLOW_UID, AIRFLOW_VAR_ASX_TICKERS, AIRFLOW_PIP_ADDITIONAL_REQUIREMENTS, TZ, ENABLED_SOLUTION_TAGS`

### overlay_heartbeat_v2

#### Command
`bash overlay_heartbeat_v2/dev-start-compose.sh`

#### Start Result
blocked

#### Observations
- Runtime did not start.
- No containers were started for this overlay.
- Airflow, Jupyter, DAG visibility, notebook reachability, and object-store checks were not reachable because the root runtime validation gate failed before container startup.

#### Result
blocked

#### Evidence
- Commands run:
  - `docker compose down`
  - `bash overlay_heartbeat_v2/dev-start-compose.sh`
- Key log excerpts:
  - `Resolved overlays (merge order):`
  - `- overlay_heartbeat_v2/dev-docker-compose.overlay-heartbeat-v2.yaml`
  - `Error: required Community env values are incomplete in /Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/.env`
  - `Missing required variables: AIRFLOW_POSTGRES_USER, AIRFLOW_POSTGRES_PASSWORD, AIRFLOW_POSTGRES_DB, AIRFLOW_ADMIN_USERNAME, AIRFLOW_ADMIN_PASSWORD, AIRFLOW_ADMIN_EMAIL, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD, JUPYTER_TOKEN, PHP_PORT, AIRFLOW_PORT, JUPYTER_PORT, MINIO_API_PORT, MINIO_CONSOLE_PORT, AWS_DEFAULT_REGION, AIRFLOW_UID, AIRFLOW_VAR_ASX_TICKERS, AIRFLOW_PIP_ADDITIONAL_REQUIREMENTS, TZ, ENABLED_SOLUTION_TAGS`

### overlay_asx_historic_csv

#### Command
`bash overlay_asx_historic_csv/dev-start-compose.sh`

#### Start Result
blocked

#### Observations
- Runtime did not start.
- No containers were started for this overlay.
- Airflow, Jupyter, PHP UI, DAG visibility, and object-store checks were not reachable because the root runtime validation gate failed before container startup.

#### Result
blocked

#### Evidence
- Commands run:
  - `docker compose down`
  - `bash overlay_asx_historic_csv/dev-start-compose.sh`
- Key log excerpts:
  - `Resolved overlays (merge order):`
  - `- overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml`
  - `Error: required Community env values are incomplete in /Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/.env`
  - `Missing required variables: AIRFLOW_POSTGRES_USER, AIRFLOW_POSTGRES_PASSWORD, AIRFLOW_POSTGRES_DB, AIRFLOW_ADMIN_USERNAME, AIRFLOW_ADMIN_PASSWORD, AIRFLOW_ADMIN_EMAIL, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD, JUPYTER_TOKEN, PHP_PORT, AIRFLOW_PORT, JUPYTER_PORT, MINIO_API_PORT, MINIO_CONSOLE_PORT, AWS_DEFAULT_REGION, AIRFLOW_UID, AIRFLOW_VAR_ASX_TICKERS, AIRFLOW_PIP_ADDITIONAL_REQUIREMENTS, TZ, ENABLED_SOLUTION_TAGS`

### overlay_kaggle_ingestion

#### Command
`bash overlay_kaggle_ingestion/dev-start-compose.sh`

#### Start Result
blocked

#### Observations
- Runtime did not start.
- No containers were started for this overlay.
- Airflow, Jupyter, PHP UI, DAG visibility, and object-store checks were not reachable because the root runtime validation gate failed before container startup.

#### Result
blocked

#### Evidence
- Commands run:
  - `docker compose down`
  - `bash overlay_kaggle_ingestion/dev-start-compose.sh`
- Key log excerpts:
  - `Resolved overlays (merge order):`
  - `- overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml`
  - `Error: required Community env values are incomplete in /Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/.env`
  - `Missing required variables: AIRFLOW_POSTGRES_USER, AIRFLOW_POSTGRES_PASSWORD, AIRFLOW_POSTGRES_DB, AIRFLOW_ADMIN_USERNAME, AIRFLOW_ADMIN_PASSWORD, AIRFLOW_ADMIN_EMAIL, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD, JUPYTER_TOKEN, PHP_PORT, AIRFLOW_PORT, JUPYTER_PORT, MINIO_API_PORT, MINIO_CONSOLE_PORT, AWS_DEFAULT_REGION, AIRFLOW_UID, AIRFLOW_VAR_ASX_TICKERS, AIRFLOW_PIP_ADDITIONAL_REQUIREMENTS, TZ, ENABLED_SOLUTION_TAGS`

### overlay_file_only_demo

#### Command
`./start-compose.sh`

#### Start Result
blocked

#### Observations
- This overlay documents no separate dev wrapper; dev mode uses the base stack command.
- Runtime did not start.
- No containers were started for this overlay.
- PHP UI reachability could not be checked because the base runtime validation gate failed before container startup.

#### Result
blocked

#### Evidence
- Commands run:
  - `docker compose down`
  - `./start-compose.sh`
- Key log excerpts:
  - `Error: required Community env values are incomplete in /Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/.env`
  - `Missing required variables: AIRFLOW_POSTGRES_USER, AIRFLOW_POSTGRES_PASSWORD, AIRFLOW_POSTGRES_DB, AIRFLOW_ADMIN_USERNAME, AIRFLOW_ADMIN_PASSWORD, AIRFLOW_ADMIN_EMAIL, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD, JUPYTER_TOKEN, PHP_PORT, AIRFLOW_PORT, JUPYTER_PORT, MINIO_API_PORT, MINIO_CONSOLE_PORT, AWS_DEFAULT_REGION, AIRFLOW_UID, AIRFLOW_VAR_ASX_TICKERS, AIRFLOW_PIP_ADDITIONAL_REQUIREMENTS, TZ, ENABLED_SOLUTION_TAGS`

## Notes

- Validation used only the dev-mode start commands documented in `docs/internal/ov_04_cross_repo_overlay_test_matrix.md`.
- The repo-scoped shutdown command `docker compose down` was executed before validation and again at the end to satisfy the single-overlay safety rule.
- Direct `docker compose down` emitted unset-variable warnings because it does not perform the stricter `.env` validation implemented by `start-compose.sh`; no overlay runtime started during OV-05.
