# OV-05R — Community Dev-Mode Overlay Remediation

## Root Cause

Community dev-mode ASX and Kaggle overlays started the base runtime successfully, but their dev overlay Compose files did not mount overlay-local DAG content into Airflow. The merged dev runtime therefore exposed only the base repo-root `./dags` bind mount inside `/opt/airflow/dags`, so `dag_asx_historic_csv` and `dag_kaggle_ingestion` were absent from Airflow.

## Files Changed

- `overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml`
- `overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml`
- `docs/internal/ov_05r_community_dev_overlay_remediation.md`
- `docs/internal/overlay_validation_task_tracker.md`

## Exact Mount Changes Made

Added explicit read-only overlay DAG directory mounts to both explicit Airflow services:

- ASX:
  - `./overlay_asx_historic_csv/dags:/opt/airflow/dags/overlay_asx_historic_csv:ro`
  - applied to `airflow-webserver`
  - applied to `airflow-scheduler`
- Kaggle:
  - `./overlay_kaggle_ingestion/dags:/opt/airflow/dags/overlay_kaggle_ingestion:ro`
  - applied to `airflow-webserver`
  - applied to `airflow-scheduler`

Note:
- A first attempt using single-file bind mounts directly to `/opt/airflow/dags/dag_<name>.py` failed under Docker Desktop because the target file path sat inside the existing base `./dags` bind mount.
- The final directory-mount approach preserves the base mount and exposes the overlay DAGs at:
  - `/opt/airflow/dags/overlay_asx_historic_csv/dag_asx_historic_csv.py`
  - `/opt/airflow/dags/overlay_kaggle_ingestion/dag_kaggle_ingestion.py`

## Validation Commands Run

### ASX

```bash
bash overlay_asx_historic_csv/dev-start-compose.sh
docker compose -f docker-compose.yaml -f overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml exec -T airflow-webserver airflow dags list
docker compose -f docker-compose.yaml -f overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml ps
bash overlay_asx_historic_csv/dev-stop-compose.sh
```

### Kaggle

```bash
bash overlay_kaggle_ingestion/dev-start-compose.sh
docker compose -f docker-compose.yaml -f overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml exec -T airflow-webserver airflow dags list
docker compose -f docker-compose.yaml -f overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml ps
bash overlay_kaggle_ingestion/dev-stop-compose.sh
```

## DAG Visibility Result

### ASX

- Result: pass
- Airflow DAG list included:
  - `dag_asx_historic_csv | /opt/airflow/dags/overlay_asx_historic_csv/dag_asx_historic_csv.py`

### Kaggle

- Result: pass
- Airflow DAG list included:
  - `dag_kaggle_ingestion | /opt/airflow/dags/overlay_kaggle_ingestion/dag_kaggle_ingestion.py`

## Airflow Health Note

- The webserver container reached running state in `docker compose ps` during both validations.
- Host and container-local `curl` probes to `/health` were inconsistent in this execution environment while the webserver was still transitioning from `health: starting`.
- Airflow CLI access via `airflow dags list` succeeded in `airflow-webserver` for both overlays, which confirms the runtime was up far enough to parse and expose the remediated DAGs.

## Out Of Scope

- `overlay_heartbeat_v2` was not remediated in this task and remains unresolved.
- Installed/archive mode was not tested in this task.
- No DAGs were triggered.

## Recommendation

Rerun OV-05 fully to refresh the Community dev-mode validation report against the remediated ASX and Kaggle dev overlay DAG mounts.
