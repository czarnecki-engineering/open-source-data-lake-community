# overlay_kaggle_ingestion_v1.0

Overlay #1 demonstrates config-driven Kaggle ingestion into MinIO-backed medallion layers, notebook-based validation, and a lightweight PHP presentation layer.

## Contents

- `config/kaggle_jobs.example.json`: example overlay job definition
- `overlay_kaggle_ingestion/docker-compose.overlay-kaggle.yaml`: overlay-specific Docker Compose additions
- `overlay_kaggle_ingestion/start-compose.sh`: overlay wrapper for the base start script
- `overlay_kaggle_ingestion/stop-compose.sh`: overlay wrapper for the base stop script
- `scripts/kaggle_to_raw.py`: Kaggle download and raw landing
- `scripts/raw_to_conformed.py`: CSV-to-Parquet conformance step
- `scripts/conformed_to_curated.py`: curated JSON summary generation
- `dags/dag_kaggle_ingestion.py`: Airflow wrapper for the three steps
- `notebooks/kaggle_connectivity_and_eda.ipynb`: validation and EDA notebook
- `php/solutions/dataset_summary.php`: curated summary renderer
- `docs/explanation.md`: overlay architecture notes

## Prerequisites

- Python 3.10+
- `pandas`
- `kaggle` 1.8.0+
- `pyarrow` or `fastparquet`
- MinIO / S3-compatible object storage
- Airflow only if you want to run the DAG
- PHP only if you want to render the summary page

Example install:

```bash
pip install pandas kaggle pyarrow
```

## Build The Archive

Create the distributable archive from the contents of `overlay_kaggle_ingestion/`:

```bash
cd overlay_kaggle_ingestion
zip -rq ../overlay_kaggle_ingestion_v1.0.zip .
cd ..
```

That zip must contain paths like:

- `config/kaggle_jobs.example.json`
- `scripts/kaggle_to_raw.py`
- `dags/dag_kaggle_ingestion.py`
- `php/solutions/dataset_summary.php`
- `overlay_kaggle_ingestion/start-compose.sh`
- `overlay_kaggle_ingestion/docker-compose.overlay-kaggle.yaml`

## Install

Install into an existing community edition checkout from the repository root:

```bash
unzip -oq overlay_kaggle_ingestion_v1.0.zip -d .
cp config/kaggle_jobs.example.json config/kaggle_jobs.json
```

Then edit `config/kaggle_jobs.json` for the dataset and MinIO object targets you want to use.

Configure Kaggle credentials in `.env`, `.env.local`, or your shell environment.

Preferred for newer Kaggle CLI versions:

```bash
export KAGGLE_API_TOKEN='your_kaggle_api_token'
```

Legacy fallback:

```bash
export KAGGLE_USERNAME='your_kaggle_username'
export KAGGLE_KEY='your_kaggle_legacy_api_key'
```

No credentials are stored in the overlay files.

## Execution

Start the base platform plus the overlay from the repository root:

```bash
./overlay_kaggle_ingestion/start-compose.sh
```

This wrapper runs the base script with the overlay compose file:

```bash
./start-compose.sh --overlay overlay_kaggle_ingestion/docker-compose.overlay-kaggle.yaml
```

Stop the overlay-aware stack:

```bash
./overlay_kaggle_ingestion/stop-compose.sh
```

For source-tree development in this feature branch, use the dev wrappers instead:

```bash
./overlay_kaggle_ingestion/dev-start-compose.sh
./overlay_kaggle_ingestion/dev-stop-compose.sh
```

Run the standard flow from the repository root:

```bash
python3 scripts/kaggle_to_raw.py --config config/kaggle_jobs.json --replace
python3 scripts/raw_to_conformed.py --config config/kaggle_jobs.json
python3 scripts/conformed_to_curated.py --config config/kaggle_jobs.json
```

Optional single-job execution:

```bash
python3 scripts/kaggle_to_raw.py --config config/kaggle_jobs.json --job sample_kaggle_csv_ingestion --replace
python3 scripts/raw_to_conformed.py --config config/kaggle_jobs.json --job sample_kaggle_csv_ingestion
python3 scripts/conformed_to_curated.py --config config/kaggle_jobs.json --job sample_kaggle_csv_ingestion
```

Optional Airflow execution:

- Ensure the Airflow environment can see the repo `scripts/` and `config/` paths.
- Trigger DAG `dag_kaggle_ingestion`.

## Validation

- Open `notebooks/kaggle_connectivity_and_eda.ipynb`
- Verify Kaggle connectivity
- Inspect MinIO raw objects in bucket `raw`
- Inspect the MinIO conformed Parquet object in bucket `conformed`
- Review or regenerate the curated summary JSON in bucket `curated`

## Presentation

The PHP page reads the curated JSON artifact mirrored from the curated bucket. It does not perform any data processing.

- Default summary path:

```text
data/curated/kaggle/stroke_prediction/stroke_prediction_summary.json
```

- Optional override via environment variable:

```bash
export KAGGLE_CURATED_SUMMARY_PATH='/absolute/path/to/summary.json'
```

- Optional override via query string:

```text
/solutions/dataset_summary.php?summary=data/curated/kaggle/stroke_prediction/stroke_prediction_summary.json
```

## Notes

- This overlay is limited to CSV-based tabular datasets.
- `kaggle_to_raw.py` prefers `KAGGLE_API_TOKEN` and falls back to `KAGGLE_USERNAME` plus `KAGGLE_KEY`.
- Raw, conformed, and curated outputs are written to MinIO buckets `raw`, `conformed`, and `curated`.
- `curated` JSON is also mirrored to `data/curated/...` for the PHP presentation page.
- The conformed step standardises column names to lowercase snake_case.
- The curated step outputs row count, columns, null counts, and basic numeric statistics.
