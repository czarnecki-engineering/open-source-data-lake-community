# Environment Configuration Update
- Repo: open-source-data-lake-community
- Mode: Execution
- Generated: 2026-04-16 21:32:10 AEST

## 1. Changes to README.md

- Added an `Environment Configuration` subsection near the startup instructions.
- Documented that Docker Compose reads `.env` automatically if present.
- Clarified that `.env.example` is a template only and added `cp .env.example .env`.
- Documented that the stack still works without `.env` by using defaults from `docker-compose.yaml`.
- Added the requested configuration precedence list and a note that some settings still require editing `docker-compose.yaml`.

## 2. Changes to RUNBOOK.md

- Added a concise `Environment Variables` section near the startup instructions.
- Clarified `.env` versus `.env.example`.
- Added `cp .env.example .env`.
- Documented that `./start-compose.sh` does not create `.env` and that overrides must exist before startup.

## 3. Changes to start-compose.sh

- Added a non-blocking warning after the repo-root checks and before Docker commands.
- The warning informs the operator when `.env` is missing and points to `cp .env.example .env`.
- No startup logic, defaults, or environment handling behaviour was changed.

## 4. Validation of `.env.example` coverage

- Checked all interpolated variables in `docker-compose.yaml` against `.env.example`.
- Confirmed `.env.example` contains all interpolated variables:
  `AIRFLOW_ADMIN_EMAIL`, `AIRFLOW_ADMIN_PASSWORD`, `AIRFLOW_ADMIN_USERNAME`, `AIRFLOW_PIP_ADDITIONAL_REQUIREMENTS`, `AIRFLOW_PORT`, `AIRFLOW_UID`, `AIRFLOW_VAR_ASX_TICKERS`, `JUPYTER_PORT`, `JUPYTER_TOKEN`, `MINIO_API_PORT`, `MINIO_CONSOLE_PORT`, `MINIO_ROOT_PASSWORD`, `MINIO_ROOT_USER`, `PHP_PORT`, `TZ`.
- Checked README and RUNBOOK wording for consistency.
- Checked that the updated docs do not imply `.env.example` is auto-used.

## 5. Notes

- `docker-compose.yaml` structure and logic were not modified.
- No new dependencies were introduced.
- Defaults were not changed.
- Some runtime settings remain hardcoded in `docker-compose.yaml` by design and are now called out explicitly in the README.
