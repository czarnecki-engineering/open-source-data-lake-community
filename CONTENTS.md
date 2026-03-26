# Contents

- `docker-compose.yaml` — Docker Compose stack for MinIO, Airflow, Jupyter, and PHP.
- `PROJECT_CONTEXT.md` — architecture-oriented summary grounded in `docker-compose.yaml`.
- `README.md` — practical orientation and run guidance.
- `RUNBOOK.md` — detailed teardown/rebuild/run steps for local use.
- `IMPLEMENTED_CAPABILITIES.md` — evidence-based capability matrix.
- `TODO.md` — current documentation and capability gaps.

- `docker/airflow/Dockerfile` — custom Airflow image with Python deps.
- `docker/jupyter/Dockerfile` — custom Jupyter image with Python deps.
- `dags/` — Airflow DAGs (heartbeat, ASX OHLCV ingestion, raw->conformed->curated).
- `notebooks/` — example Jupyter notebooks.
- `config/` — local CSV config (ASX tickers) used by DAGs.
- `php/` — FrankenPHP landing/health pages.
- `plugins/` — Airflow plugins mount (empty by default).
- `logs/` — runtime logs created by Airflow.
- `docs/` — additional documentation (if present).
