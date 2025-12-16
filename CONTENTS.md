# Contents (minio-test)

- `docker-compose.yaml` — MinIO, init job, and single-container Airflow with local mounts.
- `Dockerfile` — builds the custom Airflow image with `yfinance`, `pyarrow`, `pandas`.
- `.env` — holds `AIRFLOW_UID` (useful on Linux/WSL for volume permissions).
- `RUNBOOK.history` — actual PowerShell command history from previous runs.
- `dags/` — Airflow DAGs for heartbeat, ASX OHLCV ingestion, and raw→conformed→curated promotion.
- `plugins/` — placeholder mount for Airflow plugins (empty by default).
- `logs/` — created at runtime; Airflow writes scheduler/webserver/task logs here.
- `PROJECT_CONTEXT.md` — high-level goals, stack description, and DAG behavior.
- `README.md` — quick start, common operations, and troubleshooting.
- `RUNBOOK.md` — step-by-step, copy/pasteable workflow.
- `TODO.md` — follow-up items and ideas to expand the stack.
