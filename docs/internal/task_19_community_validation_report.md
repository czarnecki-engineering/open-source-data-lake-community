# Task 19 — Community Stage 4 Validation Report

## 1. Clean Start

- Validation target: Community runtime only.
- Branch confirmed: `feature/rearchitecture-runtime-overlay-contract`.
- Docker daemon reachable: `docker info` succeeded.
- Clean Community state prepared with scoped commands only:
  - `docker compose --env-file /tmp/task19.env down --volumes`
  - no unrelated containers or volumes were modified
- Temporary env file created from `.env.example` at `/tmp/task19.env` with only host port overrides:
  - `AIRFLOW_PORT=18080`
  - `JUPYTER_PORT=18888`
  - `PHP_PORT=18088`
  - `MINIO_API_PORT=19000`
  - `MINIO_CONSOLE_PORT=19001`
- Clean base startup command succeeded:
  - `docker compose --env-file /tmp/task19.env up -d --build`
- Result: PASS
- Evidence:
  - no missing env-variable warnings were emitted during base startup
  - no compose startup failure occurred
  - no dependency gate failed

## 2. Env Model

- `.env.example` provided all required Community runtime values.
- `start-compose.sh` currently enforces required `.env` completeness before Docker startup.
- Base runtime validation used `/tmp/task19.env`; repo-root `.env` was not modified.
- Result: PASS

## 3. Overlay Contract

- Base runtime composes through `docker-compose.yaml`.
- Representative overlay used:
  - `overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml`
- Overlay startup command succeeded:
  - `docker compose --env-file /tmp/task19.env -f docker-compose.yaml -f overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml up -d --build`
- Negative overlay validation succeeded:
  - temporary `/tmp/invalid-overlay.yaml` defining `services.airflow`
  - `./start-compose.sh --overlay /tmp/invalid-overlay.yaml`
  - emitted: `Error: logical service 'airflow' is not supported: /tmp/invalid-overlay.yaml`
- Result: PASS

## 4. Service Health

- Base runtime validation:
  - `airflow-postgres`: healthy
  - `airflow-user-init`: exited `0`
  - `airflow-webserver`: healthy
  - `airflow-scheduler`: running
  - `minio`: healthy
  - `minio-init`: exited `0`
  - `jupyter`: running and healthy
  - `php`: running and healthy
- Bucket bootstrap validation:
  - `raw`
  - `conformed`
  - `curated`
- Overlay runtime validation after representative overlay startup:
  - same service set remained stable
  - no restart loops observed
  - all restart counts remained `0`
- Result: PASS

## 5. Overlay Validation

- Overlay resolved successfully with the Community base compose file.
- No logical `airflow` service error occurred.
- No credential mismatch or missing credential failure was observed.
- Services remained stable after overlay recreation.
- Result: PASS

## 6. Negative Overlay Validation

- The invalid overlay was rejected before Docker startup progressed to env validation.
- Observed failure message:
  - `Error: logical service 'airflow' is not supported: /tmp/invalid-overlay.yaml`
- Result: PASS

## 7. Logs Review

- Base and overlay log review found:
  - no missing env-variable startup warnings
  - no credential failures
  - no dependency failures
  - no restart loops
- Non-blocking observations:
  - `docker compose` emits the pre-existing warning that `version` in `docker-compose.yaml` is obsolete
  - MinIO warns that the demo credentials from `.env.example` are default credentials
  - Airflow webserver logs include third-party package `SyntaxWarning`/`SAWarning` noise during startup
  - `airflow-postgres` logs show transient relation errors during first-run Airflow migration before tables are fully created, but the migration completed and the final runtime state was healthy
- Result: PASS

## 8. Documentation Alignment

- `README.md` and `RUNBOOK.md` align with the current Community runtime behaviour.
- Verified:
  - split Airflow services are documented
  - `.env` creation/completeness is required
  - no active Community references to SQLite or `airflow-db` remain
  - overlay rules correctly forbid `services.airflow`
  - overlay guidance correctly targets `airflow-webserver` and `airflow-scheduler`
  - MinIO credentials are documented as env-driven through `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`
- Result: PASS

## 9. Summary

- Overall Status: PASS
- Critical Issues:
  - none
- Non-Critical Observations:
  - `docker-compose.yaml` still emits a Compose deprecation warning for the top-level `version` key.
  - Startup logs include non-failing warning noise from MinIO demo credentials and third-party Airflow dependencies.
  - Initial Airflow migration produces transient PostgreSQL error lines before schema creation completes, but the final validation state is healthy.
