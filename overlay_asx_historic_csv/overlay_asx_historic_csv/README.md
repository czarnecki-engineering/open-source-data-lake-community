# overlay_asx_historic_csv_v1.0

This overlay installs an ASX historic tabular ingestion flow into an existing Open Source Data Lake Community Edition checkout.

It follows the established root-runtime plus packaged-overlay pattern:

- root runtime files are installed into the repository root by unzipping the archive
- overlay-specific runtime behavior is enabled through wrapper scripts and overlay compose files
- the PHP solution page is shown through `php/solutions.php` only when the overlay wrapper sets `ENABLED_SOLUTION_TAGS=asx-historic-csv`

## Document Location

In the source branch, this packaged README lives at:

- `overlay_asx_historic_csv/overlay_asx_historic_csv/README.md`

After building `overlay_asx_historic_csv_v1.0.zip` and unzipping into a Community Edition checkout root, it installs to:

- `overlay_asx_historic_csv/README.md`

The same install-path rule applies to `overlay_asx_historic_csv/RUNBOOK.md`.

## Contents

- `config/asx_historic_jobs.example.json`: example ASX job definition
- `scripts/asx_overlay_common.py`: shared helper for config loading, MinIO access, and curated mirror paths
- `scripts/asx_urls_to_raw.py`: HTTP/HTTPS tabular ingestion into MinIO bucket `raw`
- `scripts/raw_to_conformed.py`: CSV/XLSX/XLS tabular-to-Parquet transform into MinIO bucket `conformed`
- `scripts/conformed_to_curated.py`: curated JSON summary generation into MinIO bucket `curated` plus local mirror under `data/curated/...`
- `dags/dag_asx_historic_csv.py`: Airflow DAG wrapper for the three-stage flow
- `notebooks/asx_historic_connectivity_and_eda.ipynb`: validation and EDA notebook
- `php/solutions/asx_historic_summary.php`: curated summary renderer
- `overlay_asx_historic_csv/docker-compose.overlay-asx-historic-csv.yaml`: packaged overlay compose additions
- `overlay_asx_historic_csv/start-compose.sh`: packaged overlay start wrapper
- `overlay_asx_historic_csv/stop-compose.sh`: packaged overlay stop wrapper
- `dev-docker-compose.overlay-asx-historic-csv.yaml`: source-tree development overlay compose additions
- `dev-start-compose.sh`: source-tree development start wrapper
- `dev-stop-compose.sh`: source-tree development stop wrapper
- `docs/explanation.md`: overlay architecture notes
- `overlay_asx_historic_csv/RUNBOOK.md`: installation, archive, and validation runbook after unzip

## Source Contract

This overlay accepts simple HTTP/HTTPS tabular files:

- `.csv`
- `.xlsx`
- `.xls`

`.xlsx` is handled with `openpyxl` and legacy `.xls` is handled with `xlrd`. The conformed transform auto-selects the only sheet when the workbook has one sheet. If a workbook has multiple sheets, set `source_options.sheet_name`.

## Config Contract

Required fields per job:

- `name`
- `enabled`
- `source_urls`
- `raw_target`
- `conformed_target`
- `curated_target`

Optional fields:

- `source_options.sheet_name`
- `source_options.header_row`
- `source_options.skip_rows`

Example:

```json
{
  "jobs": [
    {
      "name": "asx_example",
      "enabled": true,
      "source_urls": [
        "https://example.com/file1.csv"
      ],
      "source_options": {
        "sheet_name": "30 June 2025"
      },
      "raw_target": "asx/historic/example/",
      "conformed_target": "asx/historic/example/example.parquet",
      "curated_target": "asx/historic/example/example_summary.json"
    }
  ]
}
```

## Build The Archive

Build the distributable archive from the contents of `overlay_asx_historic_csv/`:

```bash
cd overlay_asx_historic_csv
zip -rq ../overlay_asx_historic_csv_v1.0.zip \
  config scripts dags notebooks php overlay_asx_historic_csv
```

That zip must contain paths like:

- `config/asx_historic_jobs.example.json`
- `scripts/asx_urls_to_raw.py`
- `scripts/raw_to_conformed.py`
- `scripts/conformed_to_curated.py`
- `dags/dag_asx_historic_csv.py`
- `notebooks/asx_historic_connectivity_and_eda.ipynb`
- `php/solutions/asx_historic_summary.php`
- `overlay_asx_historic_csv/start-compose.sh`
- `overlay_asx_historic_csv/docker-compose.overlay-asx-historic-csv.yaml`

No post-unzip copy step is required.

The published runtime archive must not include:

- `dev-start-compose.sh`
- `dev-stop-compose.sh`
- `dev-docker-compose.overlay-asx-historic-csv.yaml`
- outer `.env.example`
- outer `docs/`

## Install

Install into an existing Community Edition checkout from the repository root:

```bash
unzip -oq overlay_asx_historic_csv_v1.0.zip -d .
cp config/asx_historic_jobs.example.json config/asx_historic_jobs.json
```

Then edit `config/asx_historic_jobs.json` for the real source URLs and object targets you want to use.

## Execution

For a packaged install, start the base stack plus overlay from the repository root:

```bash
bash overlay_asx_historic_csv/start-compose.sh
```

This wrapper runs:

```bash
./start-compose.sh --overlay overlay_asx_historic_csv/docker-compose.overlay-asx-historic-csv.yaml
```

Stop the packaged overlay-aware stack:

```bash
bash overlay_asx_historic_csv/stop-compose.sh
```

For source-tree development in the feature branch, use:

```bash
bash overlay_asx_historic_csv/dev-start-compose.sh
bash overlay_asx_historic_csv/dev-stop-compose.sh
```

## Optional Host-Side Execution

From the repository root:

```bash
python3 scripts/asx_urls_to_raw.py --config config/asx_historic_jobs.json --replace
python3 scripts/raw_to_conformed.py --config config/asx_historic_jobs.json
python3 scripts/conformed_to_curated.py --config config/asx_historic_jobs.json
```

Optional single-job execution:

```bash
python3 scripts/asx_urls_to_raw.py --config config/asx_historic_jobs.json --job asx_example --replace
python3 scripts/raw_to_conformed.py --config config/asx_historic_jobs.json --job asx_example
python3 scripts/conformed_to_curated.py --config config/asx_historic_jobs.json --job asx_example
```

## Airflow, Notebook, and PHP

- Airflow DAG: `dag_asx_historic_csv`
- Notebook: `notebooks/asx_historic_connectivity_and_eda.ipynb`
- PHP page: `/solutions/asx_historic_summary.php`

Important:

- the direct PHP page URL works when the file is present
- the page appears in `/solutions.php` only when the overlay compose layer sets `ENABLED_SOLUTION_TAGS=asx-historic-csv`
- this tag enablement is intentionally done in the overlay compose files, not the base stack

## Notes

- Raw, conformed, and curated outputs are written to MinIO buckets `raw`, `conformed`, and `curated`
- Curated JSON is mirrored to `data/curated/asx/historic/...` for PHP
- The conformed step standardizes column names to lowercase snake case
- Mixed identifier-like columns are normalized to string before Parquet write
- Numeric and datetime columns are preserved where the source supports them
- The curated step outputs row count, columns, dtypes, null counts, and basic numeric statistics
