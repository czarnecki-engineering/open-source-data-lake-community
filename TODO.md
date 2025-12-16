# TODO

- Add a simple `make smoke` (or script) that: builds the Airflow image, brings stack up, triggers `raw_market_ohlcv_daily_asx`, and asserts objects exist in `raw/`, `conformed/`, and `curated/`.
- Parameterise MinIO credentials/endpoint via `.env` and wire them into compose + DAG defaults instead of hardcoding `minioadmin`.
- Add DAG-level alerting (email or Slack webhook) for failures; currently silent.
- Persist Airflow metadata in Postgres (docker service) instead of SQLite to reduce scheduler fragility.
- Document and add DAG tests (e.g., unit tests for S3 key transformations and row hashing).
- Add retention/cleanup helpers for old heartbeat files and intermediate objects.
