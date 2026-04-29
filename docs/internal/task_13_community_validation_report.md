# Task 13 — Community Stage 4 Validation Report

## 1. Scope

- Repository: `/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community`
- Branch: `feature/rearchitecture-runtime-overlay-contract`
- Validation target: Community runtime only
- Explicit exclusions: Supported runtime was not started or revalidated; no runtime/configuration files were modified; no fixes/refactors/improvements were applied

## 2. Startup Method Identified

- Documented startup command: `./start-compose.sh` from repo root (`README.md:18-34`, `RUNBOOK.md:41-57`)
- Documented shutdown command: `./stop-compose.sh` and `./stop-compose.sh --volumes` (`README.md:36-50`, `RUNBOOK.md:71-97`)
- Required env setup: create repo-root `.env` from `.env.example` before startup (`README.md:21-26`, `README.md:56-69`, `RUNBOOK.md:59-69`)
- Documentation ambiguity: The startup command itself is consistent, but `README.md` still documents a legacy single-container SQLite Airflow runtime and `airflow-db` volume (`README.md:10`, `README.md:87`, `README.md:146-147`, `README.md:173`) while the actual runtime is split-service Airflow with PostgreSQL (`docker-compose.yaml:39-188`)

## 3. Env / Secrets Model Validation

- Status: FAIL
- Evidence:
  - `.env.example` defines the expected base runtime variable families: `AIRFLOW_POSTGRES_*`, `AIRFLOW_ADMIN_*`, `MINIO_*`, `JUPYTER_*`, plus shared and overlay inputs (`.env.example:1-35`)
  - Base runtime services source their credentials and ports from env variables rather than inline literals (`docker-compose.yaml:7-12`, `docker-compose.yaml:41-44`, `docker-compose.yaml:67-80`, `docker-compose.yaml:110-135`, `docker-compose.yaml:164-198`, `docker-compose.yaml:207-215`)
  - The startup wrapper only checks whether `.env` exists, not whether it is complete (`start-compose.sh:128-130`)
  - Dev and packaged overlay Jupyter services still embed credential fallbacks in runtime files: `${MINIO_ROOT_USER:-minioadmin}` and `${MINIO_ROOT_PASSWORD:-minioadmin}` (`overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml:37-40`, `overlay_kaggle_ingestion/overlay_kaggle_ingestion/docker-compose.overlay-kaggle.yaml:37-40`, `overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml:22-26`, `overlay_asx_historic_csv/overlay_asx_historic_csv/docker-compose.overlay-asx-historic-csv.yaml:22-26`)
- Findings:
  - Variable naming in the base runtime follows the agreed conventions.
  - The committed base runtime no longer hardcodes active credentials directly.
  - The overall env/secrets model still fails validation because overlay runtime files retain hardcoded credential fallbacks and the documented startup path accepted an incomplete local `.env`, which produced blank critical variables at runtime.

## 4. Overlay Contract Validation

- Status: PASS
- Evidence:
  - The base runtime exposes the contract surfaces through bind mounts for `dags/`, `scripts/`, `config/`, `data/`, `notebooks/`, and `php/` (`docker-compose.yaml:81-87`, `docker-compose.yaml:135-141`, `docker-compose.yaml:180-202`, `docker-compose.yaml:209-212`)
  - The base wrapper supports additive overlay composition via repeated `--overlay` arguments and deterministic merge order (`start-compose.sh:6-15`, `start-compose.sh:103-125`)
  - Packaged and dev overlays are represented as separate overlay compose files rather than hidden mutations inside the base compose file (`overlay_hello_world/dev-docker-compose.overlay-hello-world.yaml:1-55`, `overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml:1-50`, `overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml:1-36`, `overlay_heartbeat_v2/dev-docker-compose.overlay-heartbeat-v2.yaml:1-12`)
- Findings:
  - The Community runtime structure aligns with the overlay contract at the base/overlay boundary level.
  - Overlay activation is routed through the base wrapper, which is consistent with the contract.
  - Documentation gaps are recorded separately under Documentation Alignment.

## 5. Dev Overlay Validation

- Status: PASS
- Evidence:
  - Expected dev overlay files exist:
    - `overlay_hello_world/dev-docker-compose.overlay-hello-world.yaml`
    - `overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml`
    - `overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml`
    - `overlay_heartbeat_v2/dev-docker-compose.overlay-heartbeat-v2.yaml`
  - Dev overlay start wrappers delegate to the repo-root `start-compose.sh --overlay <file>` path (`overlay_hello_world/dev-start-compose.sh:4-18`, `overlay_kaggle_ingestion/dev-start-compose.sh:4-12`, `overlay_asx_historic_csv/dev-start-compose.sh:4-12`, `overlay_heartbeat_v2/dev-start-compose.sh:4-12`)
  - Dev overlays only target runtime services already present in the base stack: `airflow-webserver`, `airflow-scheduler`, `jupyter`, and `php` (`overlay_hello_world/dev-docker-compose.overlay-hello-world.yaml:1-55`, `overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml:1-50`, `overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml:1-36`, `overlay_heartbeat_v2/dev-docker-compose.overlay-heartbeat-v2.yaml:1-12`)
- Findings:
  - Dev overlays exist in the expected locations and are wired through documented wrapper scripts.
  - The overlays do not reintroduce a logical `airflow` service.
  - The credential fallback issue in some overlay Jupyter definitions is recorded under Env / Secrets Model Validation rather than as a structural dev-overlay failure.

## 6. Negative Validation for Logical `airflow`

- Status: FAIL
- Evidence:
  - The base runtime defines `airflow-webserver` and `airflow-scheduler`, not a logical `airflow` service (`docker-compose.yaml:96-188`)
  - Dev and packaged overlay compose files target `airflow-webserver` and `airflow-scheduler` only (`overlay_hello_world/dev-docker-compose.overlay-hello-world.yaml:1-34`, `overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml:1-26`, `overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml:1-16`, `overlay_heartbeat_v2/dev-docker-compose.overlay-heartbeat-v2.yaml:1-8`)
  - The startup wrapper explicitly rejects overlay files that define `services.airflow` (`start-compose.sh:94-100`)
  - `README.md` still describes Airflow as a single container with SQLite metadata (`README.md:10`, `README.md:173`)
- Findings:
  - Compose files and overlay wrappers satisfy the negative validation requirement.
  - The overall check still fails because repository documentation continues to assume the legacy monolithic Airflow model.

## 7. Isolated Runtime Startup Validation

- Status: FAIL
- Evidence:
  - No Community-scoped containers were running before the validation attempt.
  - The documented Community-only startup command `./start-compose.sh` was executed from the repo root.
  - Image build completed successfully.
  - Startup emitted repeated missing-variable warnings for critical values including `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `AIRFLOW_POSTGRES_USER`, `AIRFLOW_POSTGRES_PASSWORD`, `AIRFLOW_POSTGRES_DB`, `AIRFLOW_ADMIN_*`, `AIRFLOW_PORT`, `JUPYTER_PORT`, `PHP_PORT`, and others.
  - Compose created Community-scoped containers only, then failed with `service "minio-init" didn't complete successfully: exit 1`.
  - Community-scoped host ports were assigned dynamically during the failed startup attempt: MinIO console `54922`, MinIO API `54923`, Jupyter `54924`, PHP `54925`.
- Findings:
  - The isolated startup attempt did not reach the expected detached healthy-running state.
  - The immediate failure path was driven by blank env-derived runtime values accepted by the documented startup path.
  - The already-running Supported stack on default ports did not need to be stopped; because host port variables were blank in the Community startup attempt, Docker published random host ports instead of surfacing a direct documented-port conflict.

## 8. Service Health Validation

| Service | Status | Evidence | Notes |
|---|---|---|---|
| `airflow-postgres` | FAIL | Container entered `Restarting (1)`; logs reported `Database is uninitialized and superuser password is not specified.` | Core dependency never became healthy. |
| `airflow-user-init` | FAIL | Container remained `Created` because dependencies were not satisfied. | Never executed its migration/user-init command. |
| `airflow-webserver` | FAIL | Container remained `Created`. | Not started because upstream dependencies failed. |
| `airflow-scheduler` | FAIL | Container remained `Created`. | Not started because upstream dependencies failed. |
| `minio` | PASS | Container reached `Up ... (healthy)`; host endpoint `http://localhost:54923/minio/health/live` returned `HTTP/1.1 200 OK`. | Base object-store service started, but init job still failed. |
| `minio-init` | FAIL | Container exited `1`; logs reported `Unable to make bucket local/conformed. Access Denied.` | Bucket bootstrap failed. |
| `jupyter` | PASS | Container reached `Up ... (healthy)`; host endpoint `http://localhost:54924` returned `HTTP/1.1 405 Method Not Allowed` on `HEAD`, confirming an HTTP responder. | Service started on a random host port because `JUPYTER_PORT` was blank. |
| `php` | PASS | Container reached `Up ...`; host endpoint `http://localhost:54925` returned `HTTP/1.1 200 OK`. | Service started on a random host port because `PHP_PORT` was blank. |

## 9. Logs Review

- Status: FAIL
- Evidence:
  - `minio-init` log: `Unable to make bucket local/conformed. Access Denied.`
  - `airflow-postgres` log: repeated `Database is uninitialized and superuser password is not specified.`
  - `minio` log warned that it was running with default credentials `minioadmin:minioadmin`.
- Findings:
  - Logs confirm the startup failure was not a compose syntax problem; it was a runtime configuration failure.
  - No Airflow webserver/scheduler logs were available because those services never started.
  - The MinIO service itself became healthy, but the init step could not provision buckets successfully.

## 10. Documentation Alignment

- Status: FAIL
- Evidence:
  - `README.md` still states Airflow is a single-container SQLite deployment (`README.md:10`, `README.md:146-147`, `README.md:173`)
  - `README.md` still names the preserved/deleted Airflow volume as `airflow-db` (`README.md:87`, `README.md:101`, `README.md:147`)
  - `RUNBOOK.md` still documents Airflow persistence as `airflow-db` / SQLite (`RUNBOOK.md:141`, `RUNBOOK.md:164`, `RUNBOOK.md:185`)
  - `RUNBOOK.md` does not document the root wrapper’s `--overlay` activation path even though the wrapper supports it (`start-compose.sh:6-15`, `start-compose.sh:103-125`)
  - `RUNBOOK.md` includes broad cleanup commands such as `docker system prune -f` and `docker volume prune -f` (`RUNBOOK.md:241-246`), which are outside the scoped validation rules for this task
- Findings:
  - Startup/shutdown command documentation is aligned at the command-name level.
  - Runtime architecture, persistence model, and overlay usage documentation are not aligned with the current Community implementation.
  - The documented default service URLs assume complete/default env configuration, but the observed startup used random host ports because required port variables were blank.

## 11. Issues Identified

Separate findings into:

### Critical Issues

- The documented Community startup path accepted an incomplete local `.env`, leading to blank critical variables, `airflow-postgres` restart failure, and `minio-init` exit `1`; the Community runtime therefore did not start cleanly in isolation.
- Repository documentation still describes a legacy single-container SQLite Airflow runtime and `airflow-db` persistence model, which conflicts with the current split-service PostgreSQL contract.

### Non-Critical Issues

- Some overlay runtime files still include hardcoded MinIO credential fallbacks (`minioadmin`) instead of relying exclusively on env injection.
- Overlay activation support exists in `start-compose.sh`, but top-level Community documentation does not describe the `--overlay` path.
- `RUNBOOK.md` includes broad Docker cleanup commands that are not compatible with this task’s scoped-validation operating rules.

### Observations Only

- The Supported stack was already running on the documented default Community ports during validation, but it was not stopped or otherwise modified.
- Because Community port env variables were blank at runtime, Docker assigned random host ports instead of producing a direct host-port collision.
- Only Community-scoped containers and network objects were started and stopped during this task.

## 12. Overall Result

- Overall Status: FAIL
- Task 13 completion recommendation: Record Task 13 as executed with a FAIL validation result; do not mark Community Stage 4 validation as passed.
- Recommended next task: Resolve the Community runtime env completeness gap and legacy Community documentation drift, then rerun Community Stage 4 validation in isolation.
