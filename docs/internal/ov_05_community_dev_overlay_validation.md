# OV-05D — Community Dev-Mode Overlay Validation Rerun

## Branch Verification
- Branch: `feature/rearchitecture-runtime-overlay-contract`
- Result: pass

## Remediation Context

- OV-05R completed the ASX and Kaggle dev-mode DAG mount remediation.
- `overlay_asx_historic_csv` now mounts `./overlay_asx_historic_csv/dags` into Airflow at `/opt/airflow/dags/overlay_asx_historic_csv`.
- `overlay_kaggle_ingestion` now mounts `./overlay_kaggle_ingestion/dags` into Airflow at `/opt/airflow/dags/overlay_kaggle_ingestion`.
- `overlay_heartbeat_v2` remained unresolved in OV-05R and stayed out of scope for that remediation.

## Validation Summary Table

| overlay | dev_command | start_result | airflow | jupyter | php_ui | object_store | result | notes |
|---|---|---|---|---|---|---|---|---|
| `overlay_hello_world` | `bash overlay_hello_world/dev-start-compose.sh` | success | pass | pass | pass | pass | pass | `dag_hello_world` remained visible; overlay notebook/PHP/MinIO surfaces were reachable; manual object prefixes stayed empty because no DAG was triggered. |
| `overlay_heartbeat_v2` | `bash overlay_heartbeat_v2/dev-start-compose.sh` | blocked | blocked | blocked | blocked | blocked | blocked | The documented wrapper again exited before build/start with `Error: Docker daemon is not running.` |
| `overlay_asx_historic_csv` | `bash overlay_asx_historic_csv/dev-start-compose.sh` | success | pass | pass | pass | pass | pass | `dag_asx_historic_csv` is now visible from `/opt/airflow/dags/overlay_asx_historic_csv/dag_asx_historic_csv.py` after OV-05R. |
| `overlay_kaggle_ingestion` | `bash overlay_kaggle_ingestion/dev-start-compose.sh` | success | pass | pass | pass | pass | pass | `dag_kaggle_ingestion` is now visible from `/opt/airflow/dags/overlay_kaggle_ingestion/dag_kaggle_ingestion.py` after OV-05R. |
| `overlay_file_only_demo` | `./start-compose.sh` | success | pass | pass | pass | pass | pass | Base runtime started and the declared PHP page loaded; no overlay DAG or object-store surface is declared. |

## Detailed Results

### overlay_hello_world

#### Command
`bash overlay_hello_world/dev-start-compose.sh`

#### Start Result
success

#### Runtime Checks
- Airflow: runtime reached `Up`; `airflow dags list` succeeded and showed `dag_hello_world`.
- Jupyter: `http://jupyter:8888/login` returned 200 from the running Compose network.
- PHP/UI: `http://php/solutions/hello_world_summary.php` returned 200 from the running Compose network.
- Object store: MinIO API and console returned 200 from the running Compose network; buckets `raw`, `conformed`, and `curated` existed.

#### Overlay Surface Checks
- DAGs: `dag_hello_world` visible at `/opt/airflow/dags/dag_hello_world.py`.
- PHP/UI: hello world summary page loaded.
- Notebooks: Jupyter login surface was reachable; overlay notebook path is bind-mounted through the hello world overlay Jupyter config.
- Object outputs: `hello_world/` prefixes in `raw`, `conformed`, and `curated` were empty, which is expected because the manual DAG was not triggered.

#### Result
pass

#### Evidence
- Commands run:
  - `bash overlay_hello_world/dev-start-compose.sh`
  - `docker compose -f docker-compose.yaml -f overlay_hello_world/dev-docker-compose.overlay-hello-world.yaml ps`
  - `docker compose -f docker-compose.yaml -f overlay_hello_world/dev-docker-compose.overlay-hello-world.yaml exec -T airflow-webserver airflow dags list`
  - `docker compose -f docker-compose.yaml -f overlay_hello_world/dev-docker-compose.overlay-hello-world.yaml exec -T airflow-webserver python -c "...urllib..."`
  - `docker compose -f docker-compose.yaml -f overlay_hello_world/dev-docker-compose.overlay-hello-world.yaml exec -T airflow-webserver python -c "...boto3..."`
  - `bash overlay_hello_world/dev-stop-compose.sh`
- Key log/output excerpts:
  - `dag_hello_world | /opt/airflow/dags/dag_hello_world.py`
  - `"php_hello_world": {"status": 200, "content_type": "text/html; charset=UTF-8"}`
  - `"buckets": ["conformed", "curated", "raw"]`

### overlay_heartbeat_v2

#### Command
`bash overlay_heartbeat_v2/dev-start-compose.sh`

#### Start Result
blocked

#### Runtime Checks
- Airflow: blocked before startup.
- Jupyter: blocked before startup.
- PHP/UI: not declared, but base runtime never started.
- Object store: blocked before startup.

#### Overlay Surface Checks
- DAGs: not reachable because the runtime did not start.
- PHP/UI: none declared.
- Notebooks: not reachable because the runtime did not start.
- Object outputs: not reachable because the runtime did not start.

#### Result
blocked

#### Evidence
- Commands run:
  - `bash overlay_heartbeat_v2/dev-start-compose.sh`
- Key log/output excerpts:
  - `Resolved overlays (merge order):`
  - `- overlay_heartbeat_v2/dev-docker-compose.overlay-heartbeat-v2.yaml`
  - `Error: Docker daemon is not running. Start Docker Desktop and try again.`

### overlay_asx_historic_csv

#### Command
`bash overlay_asx_historic_csv/dev-start-compose.sh`

#### Start Result
success

#### Runtime Checks
- Airflow: container-local `/health` returned healthy JSON and `airflow dags list` succeeded.
- Jupyter: `http://jupyter:8888/login` returned 200 from the running Compose network.
- PHP/UI: `http://php/solutions/asx_historic_summary.php` returned 200 from the running Compose network.
- Object store: MinIO API and console returned 200 from the running Compose network; buckets `raw`, `conformed`, and `curated` existed.

#### Overlay Surface Checks
- DAGs: `dag_asx_historic_csv` visible at `/opt/airflow/dags/overlay_asx_historic_csv/dag_asx_historic_csv.py`.
- PHP/UI: ASX historic summary page loaded.
- Notebooks: Jupyter login surface was reachable; declared overlay notebook remained exposed through the overlay Jupyter configuration.
- Object outputs: the documented `asx/historic/example/` prefixes in `raw`, `conformed`, and `curated` were empty because the manual DAG was not triggered.

#### Result
pass

#### Evidence
- Commands run:
  - `bash overlay_asx_historic_csv/dev-start-compose.sh`
  - `docker compose -f docker-compose.yaml -f overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml ps`
  - `docker compose -f docker-compose.yaml -f overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml exec -T airflow-webserver airflow dags list`
  - `docker compose -f docker-compose.yaml -f overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml exec -T airflow-webserver python -c "...urllib..."`
  - `docker compose -f docker-compose.yaml -f overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml exec -T airflow-webserver python -c "...boto3..."`
  - `docker compose -f docker-compose.yaml -f overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml exec -T airflow-webserver curl -fsS http://localhost:8080/health`
  - `bash overlay_asx_historic_csv/dev-stop-compose.sh`
- Key log/output excerpts:
  - `dag_asx_historic_csv | /opt/airflow/dags/overlay_asx_historic_csv/dag_asx_historic_csv.py`
  - `"php_asx_historic": {"status": 200, "content_type": "text/html; charset=UTF-8"}`
  - `"raw_asx_historic_example": []`
  - `"scheduler": {"status": "healthy"}`

### overlay_kaggle_ingestion

#### Command
`bash overlay_kaggle_ingestion/dev-start-compose.sh`

#### Start Result
success

#### Runtime Checks
- Airflow: container-local `/health` returned healthy JSON and `airflow dags list` succeeded.
- Jupyter: `http://jupyter:8888/login` returned 200 from the running Compose network.
- PHP/UI: `http://php/solutions/dataset_summary.php` returned 200 from the running Compose network.
- Object store: MinIO API and console returned 200 from the running Compose network; buckets `raw`, `conformed`, and `curated` existed.

#### Overlay Surface Checks
- DAGs: `dag_kaggle_ingestion` visible at `/opt/airflow/dags/overlay_kaggle_ingestion/dag_kaggle_ingestion.py`.
- PHP/UI: Kaggle dataset summary page loaded.
- Notebooks: Jupyter login surface was reachable; declared overlay notebook remained exposed through the overlay Jupyter configuration.
- Object outputs: the documented `kaggle/stroke_prediction` prefixes in `raw`, `conformed`, and `curated` were empty because the manual DAG was not triggered.

#### Result
pass

#### Evidence
- Commands run:
  - `bash overlay_kaggle_ingestion/dev-start-compose.sh`
  - `docker compose -f docker-compose.yaml -f overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml ps`
  - `docker compose -f docker-compose.yaml -f overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml exec -T airflow-webserver airflow dags list`
  - `docker compose -f docker-compose.yaml -f overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml exec -T airflow-webserver python -c "...urllib..."`
  - `docker compose -f docker-compose.yaml -f overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml exec -T airflow-webserver python -c "...boto3..."`
  - `docker compose -f docker-compose.yaml -f overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml exec -T airflow-webserver curl -fsS http://localhost:8080/health`
  - `bash overlay_kaggle_ingestion/dev-stop-compose.sh`
- Key log/output excerpts:
  - `dag_kaggle_ingestion | /opt/airflow/dags/overlay_kaggle_ingestion/dag_kaggle_ingestion.py`
  - `"php_kaggle": {"status": 200, "content_type": "text/html; charset=UTF-8"}`
  - `"raw_kaggle_stroke_prediction": []`
  - `"scheduler": {"status": "healthy"}`

### overlay_file_only_demo

#### Command
`./start-compose.sh`

#### Start Result
success

#### Runtime Checks
- Airflow: runtime reached `Up`; direct `/health` probe remained flaky in this environment while the webserver was still reporting `health: starting`.
- Jupyter: `http://jupyter:8888/login` returned 200 from the running Compose network.
- PHP/UI: `http://php/solutions/file_only_demo.php` returned 200 from the running Compose network.
- Object store: MinIO API and console returned 200 from the running Compose network.

#### Overlay Surface Checks
- DAGs: no overlay DAG is declared.
- PHP/UI: file-only demo page loaded.
- Notebooks: no overlay notebook is declared.
- Object outputs: no overlay object-store surface is declared.

#### Result
pass

#### Evidence
- Commands run:
  - `./start-compose.sh`
  - `docker compose -f docker-compose.yaml ps`
  - `docker compose -f docker-compose.yaml exec -T airflow-webserver python -c "...urllib..."`
  - `./stop-compose.sh`
- Key log/output excerpts:
  - `"php_file_only_demo": {"status": 200, "content_type": "text/html; charset=UTF-8"}`
  - `STATUS ... airflow-webserver ... Up ... (health: starting)`

## Comparison With Initial OV-05

- Resolved:
  - `overlay_asx_historic_csv` no longer fails on missing DAG visibility; `dag_asx_historic_csv` is now present in Airflow.
  - `overlay_kaggle_ingestion` no longer fails on missing DAG visibility; `dag_kaggle_ingestion` is now present in Airflow.
- Unchanged:
  - `overlay_hello_world` continues to pass.
  - `overlay_file_only_demo` continues to pass.
  - `overlay_heartbeat_v2` remains blocked at the same documented wrapper error before startup.
- ASX/Kaggle remediation succeeded in the full rerun.

## Validation Not Performed

- No DAGs were triggered for any overlay because the declared overlay DAGs for hello world, ASX historic, and Kaggle ingestion are manual and this rerun was limited to startup and surface visibility.
- No installed/archive mode checks were performed; those belong to OV-06.

## Recommended Next Task

OV-06 — Community installed-mode overlay validation
