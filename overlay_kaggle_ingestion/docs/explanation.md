# Overlay Architecture

## Purpose

`overlay_kaggle_ingestion` is a self-contained additive overlay that demonstrates a simple external ingestion path for CSV-based Kaggle datasets:

1. Config-driven job definition
2. Raw landing in MinIO object storage
3. Conformed Parquet output in MinIO
4. Curated JSON summary artifact in MinIO
5. Notebook validation
6. PHP presentation

## Config Contract

The overlay expects `config/kaggle_jobs.json` with a top-level `jobs` list. Each enabled job includes:

- `name`: logical job identifier
- `enabled`: execution flag
- `dataset`: Kaggle dataset slug such as `owner/dataset-name`
- `raw_target`: object prefix inside bucket `raw`
- `conformed_target`: Parquet object key inside bucket `conformed`
- `curated_target`: curated JSON object key inside bucket `curated`

Credentials are never stored in the config. The ingestion step reads:

- `KAGGLE_API_TOKEN` preferred
- `KAGGLE_USERNAME`
- `KAGGLE_KEY`

## Pipeline Stages

### 1. `kaggle_to_raw.py`

- Reads enabled jobs from config
- Loads `.env` and `.env.local` if present
- Authenticates with the Kaggle API
- Downloads and unzips the configured dataset
- Uploads extracted files into the configured raw bucket prefix
- Supports `--job` filtering and `--replace` for a clean reload
- Prefers access-token auth and falls back to legacy username/key auth

### 2. `raw_to_conformed.py`

- Scans the configured MinIO raw prefix for CSV objects
- Loads objects with pandas
- Standardises column names to lowercase snake_case
- Adds source lineage columns
- Writes a single Parquet object to the configured conformed target

### 3. `conformed_to_curated.py`

- Reads the conformed Parquet object
- Computes row count and column inventory
- Computes null counts
- Computes lightweight numeric statistics
- Writes a curated JSON object
- Mirrors the curated JSON to `data/curated/...` for the PHP page

## DAG Design

`dag_kaggle_ingestion.py` intentionally stays thin. It calls the three overlay scripts in order using Airflow `PythonOperator` tasks rather than duplicating transformation logic inside the DAG.

This keeps the notebook, CLI flow, and DAG flow aligned around the same scripts and config contract.

## Notebook Role

`kaggle_connectivity_and_eda.ipynb` is a validation artifact, not a production transformation step. It is used to:

- confirm Kaggle authentication
- inspect dataset files
- review MinIO raw objects
- perform quick EDA
- optionally regenerate the curated summary

## PHP Role

`solutions/dataset_summary.php` reads the curated JSON output and renders:

- dataset name
- job name
- row count
- columns
- null counts
- numeric metrics

It does not transform raw data, and it only depends on the generated curated artifact mirrored from MinIO.

## Operational Notes

- The overlay is additive only and does not modify existing platform code.
- The overlay assumes tabular CSV inputs only.
- Parquet output requires `pyarrow` or `fastparquet`.
- The DAG assumes repository paths are mounted into the Airflow environment.
- The overlay uses MinIO buckets `raw`, `conformed`, and `curated` as the medallion storage contract.
