# RUNBOOK — overlay_kaggle_ingestion

1. Build the archive from `overlay_kaggle_ingestion/` with:

```bash
cd overlay_kaggle_ingestion
zip -rq ../overlay_kaggle_ingestion_v1.0.zip \
  config scripts dags notebooks php overlay_kaggle_ingestion
```

2. Unzip the archive into the root of an existing community checkout:

```bash
unzip -oq overlay_kaggle_ingestion_v1.0.zip -d .
cp config/kaggle_jobs.example.json config/kaggle_jobs.json
```

3. Provide Kaggle credentials in `.env` or your shell environment.

4. Start the packaged overlay:

```bash
bash overlay_kaggle_ingestion/start-compose.sh
```

This runs:

```bash
./start-compose.sh --overlay overlay_kaggle_ingestion/docker-compose.overlay-kaggle.yaml
```

5. Validate:

- Airflow, Jupyter, MinIO, and PHP start cleanly
- `php/solutions/dataset_summary.php` is present
- `ENABLED_SOLUTION_TAGS=kaggle` is applied to the PHP service
- the notebook `notebooks/kaggle_connectivity_and_eda.ipynb` is present

6. Stop with:

```bash
bash overlay_kaggle_ingestion/stop-compose.sh
```
