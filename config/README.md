# ASX200 ticker config

The ASX200 DAGs rely on a local CSV named `asx200_tickers.csv` in this folder. The file is ignored in git, so to run the DAGs you must create and populate `config/asx200_tickers.csv` locally before execution. If the file is missing, the ASX200 DAGs will not have any tickers to process.
