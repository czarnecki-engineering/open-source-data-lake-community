# ASX200 ticker config

The ASX200 DAGs rely on a local CSV named `asx200_tickers.csv` in this folder. The file is ignored in git, so to run the DAGs you must create and populate `config/asx200_tickers.csv` locally before execution. If the file is missing, the ASX200 DAGs will not have any tickers to process.

## Manual Ticker Configuration (ASX Data Pipeline)

- The ASX ingestion DAG `asx200_ohlcv_daily_to_raw` requires `config/asx200_tickers.csv`.
- This file is not provided by default and must be created manually by the operator.
- Purpose: control the number of tickers queried from yFinance and avoid excessive or abusive API usage.
- Behaviour:
  - If the file is missing, the DAG will fail.
  - This is expected and does not indicate a problem with the platform.
- The platform is considered healthy if:
  - services start successfully,
  - the Airflow UI is accessible,
  - heartbeat DAGs are running.
- Sample starting points:
  - `config/asx200_tickers_top3.csv`
  - `config/asx200_tickers_top100.csv`
