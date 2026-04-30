# ASX200 ticker config

This folder holds the local ticker CSV used by the ASX ingestion DAGs.

- Expected runtime filename: `config/asx200_tickers.csv`
- Tracked sample files:
  - `config/asx200_tickers_top3.csv`
  - `config/asx200_tickers_top100.csv`

`config/asx200_tickers.csv` is intentionally not tracked in git. Create it locally from one of the sample files before running the ASX DAGs.
