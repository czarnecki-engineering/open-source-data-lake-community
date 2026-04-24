# Overlay #2 Prompt: ASX Historic CSV Ingestion

Use this prompt to start a new chat for Overlay #2 in the `oss-data-lake-community` repository.

---

You are operating in the `oss-data-lake-community` repository.

## CONTEXT

We have already implemented and validated **Overlay #1: Kaggle Ingestion**.

For Overlay #2, we want to reuse the same architecture, packaging model, and testing discipline, but the source system is different:

- source data is a set of historic ASX-related CSV files available at HTTP/HTTPS URLs
- data should land in MinIO-backed medallion layers
- notebook validation and PHP presentation should follow the same lightweight pattern

This overlay must be built as a **standardised, installable overlay** for the Open Data Lake Community Edition.

All work must be performed in a new branch:

```text
feature/overlay-asx_historic_csv
```

All outputs must be additive only. Do not modify core platform code unless a generic platform improvement is clearly required and separately justified.

---

## IMPORTANT LEARNINGS FROM OVERLAY #1

You must follow these lessons from the Kaggle overlay:

1. The overlay must be **MinIO-backed**, not filesystem-backed, for the raw, conformed, and curated medallion layers.
2. The overlay archive must be built from the **contents** of the overlay folder, not from the parent folder.
3. A simple unzip into the installed community root must place files into the correct runtime locations with **no post-unzip copy step**.
4. Overlay-specific compose and wrapper files must live under the installed runtime path:
   - `./overlay_<name>/...`
5. Base root scripts from `main` must not be overwritten by the overlay archive.
6. Root runtime files such as `scripts/`, `dags/`, `config/`, `notebooks/`, and `php/solutions/` are valid, because after unzip they become part of the working community installation.
7. For source-tree development, provide **dev wrappers** and a **dev overlay compose file** if the packaged overlay paths are not directly executable from the feature branch.
8. The real acceptance test is:
   - clean `main`-based checkout
   - apply generic `main` changes only if needed
   - build archive from overlay contents
   - unzip archive into clean checkout
   - run the actual user commands
   - verify Airflow, MinIO, Jupyter, and PHP

---

## DEVELOPMENT MODE

During development, work directly in the repository root runtime paths:

- `/config/`
- `/scripts/`
- `/dags/`
- `/notebooks/`
- `/php/`

The packaged overlay copy under `overlay_asx_historic_csv/` is the distributable source tree and must mirror the final installed layout.

---

## OBJECTIVE

Create a fully working, installable overlay that:

1. Reads a JSON config from `./config/`
2. Downloads one or more historic ASX CSV files from configured URLs
3. Lands them into the `raw` MinIO bucket
4. Produces a conformed tabular dataset in the `conformed` MinIO bucket
5. Produces curated JSON summary artifacts in the `curated` MinIO bucket
6. Provides a notebook for validation and EDA
7. Provides a PHP page in `php/solutions/` to display the results

---

## PROPOSED OVERLAY NAME

Use this overlay name unless there is a strong reason to change it:

```text
overlay_asx_historic_csv
```

---

## OVERLAY CONTRACT

Create this packaged structure:

```text
overlay_asx_historic_csv/

  README.md

  /config/
    asx_historic_jobs.example.json

  /scripts/
    asx_urls_to_raw.py
    raw_to_conformed.py
    conformed_to_curated.py
    asx_overlay_common.py

  /dags/
    dag_asx_historic_csv.py

  /notebooks/
    asx_historic_connectivity_and_eda.ipynb

  /php/
    /solutions/
      asx_historic_summary.php

  /docs/
    explanation.md

  /overlay_asx_historic_csv/
    docker-compose.overlay-asx-historic-csv.yaml
    start-compose.sh
    stop-compose.sh
    /docker/
      /airflow/
        Dockerfile
      /jupyter/
        Dockerfile
```

Also provide source-tree-only development helpers if needed:

```text
overlay_asx_historic_csv/
  dev-docker-compose.overlay-asx-historic-csv.yaml
  dev-start-compose.sh
  dev-stop-compose.sh
```

---

## CONFIG DESIGN

Create `asx_historic_jobs.example.json`.

Each job should support:

- `name`
- `enabled`
- `source_urls`
- `raw_target`
- `conformed_target`
- `curated_target`

Do not commit secrets.

Use environment variables for any remote or storage auth.

---

## STORAGE CONTRACT

This overlay must write to MinIO buckets:

- `raw`
- `conformed`
- `curated`

Examples:

- `raw/asx/historic/...csv`
- `conformed/asx/historic/...parquet`
- `curated/asx/historic/...summary.json`

If PHP needs local file access, curated JSON may also be mirrored to `data/curated/...`, but MinIO remains the source of truth.

---

## IMPLEMENTATION REQUIREMENTS

### 1. Ingestion Script

`asx_urls_to_raw.py`

- read config JSON
- download configured CSV files from HTTP/HTTPS URLs
- validate non-empty responses and expected content type or extension
- upload raw files into MinIO bucket `raw`
- support replace/overwrite mode safely
- emit a clear JSON summary

### 2. Conformed Script

`raw_to_conformed.py`

- read CSV objects from MinIO `raw`
- use pandas
- standardise column names to lowercase snake_case
- preserve source lineage such as `source_object_key`
- write Parquet into MinIO `conformed`
- emit a clear JSON summary

### 3. Curated Script

`conformed_to_curated.py`

- read Parquet from MinIO `conformed`
- calculate row count, columns, null counts, and basic numeric stats
- write JSON to MinIO `curated`
- optionally mirror curated JSON to local `data/curated/...` for PHP
- emit a clear JSON summary

### 4. Shared Helper

`asx_overlay_common.py`

- config loading
- dotenv loading
- job normalisation
- MinIO / S3 client helpers
- prefix deletion and list helpers
- curated mirror path helper

### 5. DAG

`dag_asx_historic_csv.py`

- sequential tasks:
  - ingestion
  - raw to conformed
  - conformed to curated
- no complex scheduling required

### 6. Notebook

`asx_historic_connectivity_and_eda.ipynb`

- verify URL accessibility
- verify MinIO object presence
- load raw CSV from MinIO
- load conformed Parquet from MinIO
- load curated JSON from MinIO
- include:
  - shape
  - head
  - nulls
  - simple aggregations
  - univariate plots
  - bivariate plots

### 7. PHP Page

`php/solutions/asx_historic_summary.php`

- follow the existing page style used by `php/index.php`, `php/health.php`, and `php/solutions.php`
- include metadata comments:
  - `Solution Title: ...`
  - `Solution Summary: ...`
  - `Solution Tag: asx-historic-csv`
- read curated JSON only
- perform no data processing beyond display formatting

---

## PHP SOLUTIONS CONTRACT

The repository now supports a generic solutions listing page at:

```text
php/solutions.php
```

Overlay-specific solution pages must:

- live under `php/solutions/`
- include metadata comments near the top of the file:
  - `Solution Title: ...`
  - `Solution Summary: ...`
  - optional `Solution Tag: ...`

Overlay compose should enable the relevant solution tag in the PHP container, for example:

```text
ENABLED_SOLUTION_TAGS=asx-historic-csv
```

Without the overlay, the generic `php/solutions.php` page should not list the overlay solution.

---

## COMPOSE / INSTALLATION MODEL

The base platform remains in `main`.

The overlay must be installable by:

1. creating an archive from the **contents** of `overlay_asx_historic_csv/`
2. unzipping that archive into the community repo root

The installed commands should be:

```bash
./overlay_asx_historic_csv/start-compose.sh
./overlay_asx_historic_csv/stop-compose.sh
```

Which should wrap:

```bash
./start-compose.sh --overlay overlay_asx_historic_csv/docker-compose.overlay-asx-historic-csv.yaml
./stop-compose.sh --overlay overlay_asx_historic_csv/docker-compose.overlay-asx-historic-csv.yaml
```

The packaged overlay compose file must use installed-path layout.

If those paths are not directly usable in the source tree, provide source-tree dev helpers:

```bash
./overlay_asx_historic_csv/dev-start-compose.sh
./overlay_asx_historic_csv/dev-stop-compose.sh
```

---

## MAIN BRANCH RULE

Only move generic platform improvements to `main`.

Examples of acceptable generic `main` changes:

- enhancements to `start-compose.sh`
- enhancements to `stop-compose.sh`
- generic PHP solutions index or menu changes

Do not move overlay-specific code into `main`.

---

## EXECUTION AND TESTING REQUIREMENTS

You must validate in three stages:

### Stage 1: Host-side Pipeline

Verify:

- ingestion script works
- conformed script works
- curated script works

### Stage 2: Source-tree Compose Validation

If dev wrappers are provided, verify:

- base start/stop works
- overlay dev start/stop works

### Stage 3: Real Packaging Test

This is mandatory.

You must:

1. build the overlay archive from `overlay_asx_historic_csv/`
2. create a clean `main`-based temporary checkout
3. unzip the overlay archive into that checkout
4. run:
   - `./overlay_asx_historic_csv/start-compose.sh`
   - `./overlay_asx_historic_csv/stop-compose.sh`
5. verify:
   - Airflow DAG runs
   - raw objects appear in MinIO
   - conformed objects appear in MinIO
   - curated objects appear in MinIO
   - notebook executes
   - PHP page renders
   - generic `php/solutions.php` shows the ASX solution only when overlay mode is active

### Stage 4: Base Compatibility Check

If any generic files are changed for `main`, validate that plain base:

```bash
./start-compose.sh
./stop-compose.sh
```

still works without the overlay.

---

## DOCUMENTATION DELIVERABLES

Produce:

1. overlay README
2. docs/explanation.md
3. explicit archive build/install/run commands
4. exact overlay start command
5. exact dev-start command if provided
6. validation notes

---

## NEXT TASK

Start by creating the overlay directory structure and implement:

- `asx_historic_jobs.example.json`
- `asx_urls_to_raw.py`
- `asx_overlay_common.py`

Do not proceed further until these are internally consistent.
