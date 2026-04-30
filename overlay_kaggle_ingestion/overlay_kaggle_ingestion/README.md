# overlay_kaggle_ingestion_v1.0

This overlay installs a Kaggle ingestion flow into an existing Open Source Data Lake Community checkout.

It follows the additive payload plus packaged-runtime pattern:

- runtime files install into the normal repository folders
- packaged overlay execution is enabled through `overlay_kaggle_ingestion/start-compose.sh`
- the PHP solution page is shown in `solutions.php` when the overlay compose file sets `ENABLED_SOLUTION_TAGS=kaggle`

## Contents

- `config/kaggle_jobs.example.json`
- `scripts/kaggle_overlay_common.py`
- `scripts/kaggle_to_raw.py`
- `scripts/raw_to_conformed.py`
- `scripts/conformed_to_curated.py`
- `dags/dag_kaggle_ingestion.py`
- `notebooks/kaggle_connectivity_and_eda.ipynb`
- `php/solutions/dataset_summary.php`
- `overlay_kaggle_ingestion/docker-compose.overlay-kaggle.yaml`
- `overlay_kaggle_ingestion/start-compose.sh`
- `overlay_kaggle_ingestion/stop-compose.sh`

## Build The Archive

Build the distributable archive from the contents of `overlay_kaggle_ingestion/`:

```bash
cd overlay_kaggle_ingestion
zip -rq ../overlay_kaggle_ingestion_v1.0.zip \
  config scripts dags notebooks php overlay_kaggle_ingestion
cd ..
```

Validated archive contents include:

- `config/`
- `scripts/`
- `dags/`
- `notebooks/`
- `php/`
- `overlay_kaggle_ingestion/`

The published runtime archive must not include:

- `dev-start-compose.sh`
- `dev-stop-compose.sh`
- `dev-docker-compose.overlay-kaggle.yaml`
- outer `.env.example`
- outer `docs/`

## Install

Install into an existing community checkout from the repository root:

```bash
unzip -oq overlay_kaggle_ingestion_v1.0.zip -d .
cp config/kaggle_jobs.example.json config/kaggle_jobs.json
```

The validated install contract is that `config/kaggle_jobs.example.json` exists immediately after `unzip` with no manual file moves.

Configure Kaggle credentials in `.env` or your shell environment, then start with:

```bash
bash overlay_kaggle_ingestion/start-compose.sh
```

After a short Airflow warm-up, validate the installed overlay with:

```bash
curl http://localhost:8080/health
docker compose -f docker-compose.yaml -f overlay_kaggle_ingestion/docker-compose.overlay-kaggle.yaml logs airflow-scheduler
```
