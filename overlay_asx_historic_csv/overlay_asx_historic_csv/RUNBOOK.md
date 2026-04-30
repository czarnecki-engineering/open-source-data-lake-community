# RUNBOOK — overlay_asx_historic_csv

This runbook describes the validated packaging and installation path for `overlay_asx_historic_csv`.

The critical install contract is:

1. build the overlay zip from `overlay_asx_historic_csv/`
2. unzip the archive into the root of an existing Open Source Data Lake Community Edition checkout
3. start the stack through the overlay wrapper

No post-unzip copy of overlay files is required.

## Document Location

In the source branch, this packaged runbook lives at:

- `overlay_asx_historic_csv/overlay_asx_historic_csv/RUNBOOK.md`

After building `overlay_asx_historic_csv_v1.0.zip` and unzipping into a Community Edition checkout root, it installs to:

- `overlay_asx_historic_csv/RUNBOOK.md`

## Preconditions

- Docker Desktop or Docker Engine is running
- `docker compose` v2 is available
- `zip` and `unzip` are available
- you have a Community Edition checkout with:
  - `docker-compose.yaml`
  - `start-compose.sh`
  - `stop-compose.sh`
  - `php/solutions.php`

## Files Installed By The Archive

After unzip into the repository root, these key files should exist:

- `config/asx_historic_jobs.example.json`
- `scripts/asx_overlay_common.py`
- `scripts/asx_urls_to_raw.py`
- `scripts/raw_to_conformed.py`
- `scripts/conformed_to_curated.py`
- `dags/dag_asx_historic_csv.py`
- `notebooks/asx_historic_connectivity_and_eda.ipynb`
- `php/solutions/asx_historic_summary.php`
- `overlay_asx_historic_csv/docker-compose.overlay-asx-historic-csv.yaml`
- `overlay_asx_historic_csv/start-compose.sh`
- `overlay_asx_historic_csv/stop-compose.sh`

## Build The Archive

From the feature branch repository root:

```bash
cd overlay_asx_historic_csv
zip -rq ../overlay_asx_historic_csv_v1.0.zip \
  config scripts dags notebooks php overlay_asx_historic_csv
```

Do not publish:

- `dev-start-compose.sh`
- `dev-stop-compose.sh`
- `dev-docker-compose.overlay-asx-historic-csv.yaml`
- outer `.env.example`
- outer `docs/`

## Install Into A Clean Community Checkout

From the clean checkout root:

```bash
unzip -oq overlay_asx_historic_csv_v1.0.zip -d .
cp config/asx_historic_jobs.example.json config/asx_historic_jobs.json
```

Edit `config/asx_historic_jobs.json` with the source URLs you want to process.

For the validated test flow, the real workbook URL used was:

```text
https://files.marketindex.com.au/files/data-downloads/30-june-2025.xlsx
```

The tested job shape was:

```json
{
  "jobs": [
    {
      "name": "asx_marketindex_2025_06_30",
      "enabled": true,
      "source_urls": [
        "https://files.marketindex.com.au/files/data-downloads/30-june-2025.xlsx"
      ],
      "raw_target": "asx/historic/marketindex/2025-06-30/",
      "conformed_target": "asx/historic/marketindex/2025-06-30/marketindex_2025_06_30.parquet",
      "curated_target": "asx/historic/marketindex/2025-06-30/marketindex_2025_06_30_summary.json"
    }
  ]
}
```

## Start The Packaged Overlay

From the clean checkout root:

```bash
bash overlay_asx_historic_csv/start-compose.sh
```

This runs:

```bash
./start-compose.sh --overlay overlay_asx_historic_csv/docker-compose.overlay-asx-historic-csv.yaml
```

The overlay compose layer is responsible for:

- mounting `scripts/` and `data/` into Airflow
- mounting `config/`, `scripts/`, and `data/` into Jupyter
- mounting `data/` into PHP
- setting `ENABLED_SOLUTION_TAGS=asx-historic-csv` in the PHP service

Stop the packaged stack with:

```bash
bash overlay_asx_historic_csv/stop-compose.sh
```

## Validation Sequence

Validate in this order.

### 1. Ingestion

Host-side or DAG-driven ingestion should land the source in MinIO bucket `raw`.

Expected object for the validated workbook test:

```text
raw/asx/historic/marketindex/2025-06-30/30-june-2025.xlsx
```

### 2. Conformed Transform

`raw_to_conformed.py` should write a Parquet object to bucket `conformed`.

Expected object:

```text
conformed/asx/historic/marketindex/2025-06-30/marketindex_2025_06_30.parquet
```

The validated conformed result preserved useful types:

- `asx_code`: `string`
- `last_price`: `Float64`
- `business_date`: `datetime64[ns]`

### 3. Curated Summary

`conformed_to_curated.py` should write a JSON summary to bucket `curated` and mirror it locally.

Expected object and mirror path:

```text
curated/asx/historic/marketindex/2025-06-30/marketindex_2025_06_30_summary.json
data/curated/asx/historic/marketindex/2025-06-30/marketindex_2025_06_30_summary.json
```

### 4. Airflow DAG

Use DAG:

```text
dag_asx_historic_csv
```

Validated sequence:

1. `asx_urls_to_raw`
2. `raw_to_conformed`
3. `conformed_to_curated`

The DAG was proven with `airflow dags test` and completed successfully end to end.

### 5. Notebook

Open:

```text
notebooks/asx_historic_connectivity_and_eda.ipynb
```

Validated notebook checks:

- source URL accessibility
- raw object presence in MinIO
- conformed Parquet load
- curated JSON load
- univariate and bivariate EDA
- missing `business_date` checks

Validated finding:

- `1092` rows had missing `business_date`
- all `1092` of those also had missing `last_price`
- `0` rows had missing `business_date` with a present `last_price`

That indicates source semantics, not a transform bug.

### 6. PHP

Direct page:

```text
/solutions/asx_historic_summary.php
```

Solutions page:

```text
/solutions.php
```

Contract detail:

- direct page routing only requires the file to exist
- `/solutions.php` shows tagged pages only when the PHP container has:

```text
ENABLED_SOLUTION_TAGS=asx-historic-csv
```

That variable is set by the overlay compose file, not by the base stack.

## Clean Packaging Test Pattern

Use this exact pattern:

1. stop any running stack
2. build `overlay_asx_historic_csv_v1.0.zip`
3. create a clean `main`-based checkout
4. unzip the archive into that checkout root
5. create `config/asx_historic_jobs.json`
6. start through `bash overlay_asx_historic_csv/start-compose.sh`
7. validate raw, conformed, curated, DAG, notebook, and PHP
8. stop the packaged stack

## Observed Validated Output

For the Market Index workbook test:

- raw object size: `235156` bytes
- conformed object size: `124333` bytes
- curated object size: `1416` bytes
- conformed row count: `4709`
- curated column count: `9`

## Troubleshooting

### Page visible directly but not in `/solutions.php`

Cause:

- `Solution Tag` is set in the PHP page
- `ENABLED_SOLUTION_TAGS` does not include `asx-historic-csv`

Fix:

- start the stack through the overlay wrapper, not only the base stack:
  `bash overlay_asx_historic_csv/start-compose.sh`

### Excel ingestion works but conformed step fails

Check:

- `openpyxl` is available in the runtime environment
- `xlrd` is available in the runtime environment for legacy `.xls`
- the workbook has one sheet, or `source_options.sheet_name` is configured

### Mixed-type Parquet write failure

Handled by the current overlay:

- identifier-like mixed columns are normalized to string before Parquet write

### Curated JSON not visible to PHP

Check:

- local mirror exists under `data/curated/asx/historic/...`
- PHP has `./data:/app/data:ro`
- stack was started through the overlay compose wrapper
