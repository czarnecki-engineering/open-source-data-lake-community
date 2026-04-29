# OV-05 — Community Dev-Mode Overlay Validation

## Branch Verification
- Branch: `feature/rearchitecture-runtime-overlay-contract`
- Result: pass

## Validation Summary Table

| overlay | dev_command | start_result | airflow | jupyter | php_ui | object_store | result | notes |
|---|---|---|---|---|---|---|---|---|
| `overlay_hello_world` | `bash overlay_hello_world/dev-start-compose.sh` | success | pass | pass | pass | pass | pass | Runtime started; `dag_hello_world` was visible; MinIO buckets existed but no `hello_world/` keys were present because the manual DAG was not triggered. |
| `overlay_heartbeat_v2` | `bash overlay_heartbeat_v2/dev-start-compose.sh` | blocked | blocked | blocked | blocked | blocked | blocked | The documented wrapper twice exited before build/start with `Error: Docker daemon is not running`, even though `docker info` succeeded outside the wrapper and other overlays started normally. |
| `overlay_asx_historic_csv` | `bash overlay_asx_historic_csv/dev-start-compose.sh` | success | pass | pass | pass | pass | fail | Base runtime came up cleanly, but declared DAG `dag_asx_historic_csv` was not present in Airflow. |
| `overlay_kaggle_ingestion` | `bash overlay_kaggle_ingestion/dev-start-compose.sh` | success | pass | pass | pass | pass | fail | Base runtime came up cleanly, but declared DAG `dag_kaggle_ingestion` was not present in Airflow. |
| `overlay_file_only_demo` | `./start-compose.sh` | success | pass | pass | pass | pass | pass | Base runtime started and the declared PHP page loaded successfully; no overlay DAG, notebook, or object-store surface is declared. |

## Detailed Results

### overlay_hello_world

#### Command
`bash overlay_hello_world/dev-start-compose.sh`

#### Start Result
success

#### Observations
- Container status: all base services reached `Up` and the webserver became healthy.
- UI reachability:
  - Airflow health: `GET /health` returned 200 from `http://localhost:8080/health`.
  - Jupyter login page returned 200 from `http://jupyter:8888/login` via in-network probe.
  - PHP page returned 200 from `http://php/solutions/hello_world_summary.php` via in-network probe.
  - MinIO API and console returned 200 from `http://minio:9000/minio/health/live` and `http://minio:9001` via in-network probe.
- DAG visibility: `dag_hello_world` was listed in Airflow at `/opt/airflow/dags/dag_hello_world.py`.
- Object-store evidence: buckets `raw`, `conformed`, and `curated` existed; `hello_world/` prefixes were empty at validation time because the manual DAG was not triggered.
- Logs: Airflow webserver listened on `0.0.0.0:8080`; Jupyter reported it was serving notebooks; MinIO advertised both API and console endpoints; PHP started cleanly under FrankenPHP.

#### Result
pass

#### Evidence
- Commands run:
  - `bash overlay_hello_world/dev-start-compose.sh`
  - `docker compose -f docker-compose.yaml -f overlay_hello_world/dev-docker-compose.overlay-hello-world.yaml ps`
  - `curl -fsS http://localhost:8080/health`
  - `docker compose -f docker-compose.yaml -f overlay_hello_world/dev-docker-compose.overlay-hello-world.yaml exec -T airflow-webserver airflow dags list`
  - `docker compose -f docker-compose.yaml -f overlay_hello_world/dev-docker-compose.overlay-hello-world.yaml exec -T airflow-webserver python -c "...urllib..."` for Jupyter, PHP, and MinIO reachability
  - `docker compose -f docker-compose.yaml -f overlay_hello_world/dev-docker-compose.overlay-hello-world.yaml exec -T airflow-webserver python -c "...boto3..."` for buckets and `hello_world/` prefixes
  - `bash overlay_hello_world/dev-stop-compose.sh`
- Key log excerpts:
  - `Stack is starting. Default access URLs...`
  - `dag_hello_world | /opt/airflow/dags/dag_hello_world.py`
  - `"buckets": ["conformed", "curated", "raw"]`
  - `"raw_hello_world": []`

### overlay_heartbeat_v2

#### Command
`bash overlay_heartbeat_v2/dev-start-compose.sh`

#### Start Result
blocked

#### Observations
- Runtime did not start.
- The documented wrapper failed twice before image build or container startup.
- This was not a repo-wide Docker outage: `docker info` succeeded immediately after the first failure, and `overlay_asx_historic_csv`, `overlay_kaggle_ingestion`, and `overlay_file_only_demo` all started later in the same validation run.

#### Result
blocked

#### Evidence
- Commands run:
  - `bash overlay_heartbeat_v2/dev-start-compose.sh`
  - `docker info`
  - `docker ps`
  - `bash overlay_heartbeat_v2/dev-start-compose.sh` (second documented retry after confirming Docker was available)
- Key log excerpts:
  - `Resolved overlays (merge order):`
  - `- overlay_heartbeat_v2/dev-docker-compose.overlay-heartbeat-v2.yaml`
  - `Error: Docker daemon is not running. Start Docker Desktop and try again.`
  - `Server Version: 29.1.2`

### overlay_asx_historic_csv

#### Command
`bash overlay_asx_historic_csv/dev-start-compose.sh`

#### Start Result
success

#### Observations
- Container status: all base services reached `Up`, and the Airflow webserver became healthy.
- UI reachability:
  - Airflow health returned 200 from `http://localhost:8080/health`.
  - Jupyter login returned 200 from `http://jupyter:8888/login` via in-network probe.
  - PHP page returned 200 from `http://php/solutions/asx_historic_summary.php` via in-network probe.
  - MinIO API and console returned 200 via in-network probe.
- DAG visibility: declared DAG `dag_asx_historic_csv` was not present in `airflow dags list`.
- Object-store evidence: buckets `raw`, `conformed`, and `curated` existed; the documented example prefixes under `asx/historic/example/` were empty.
- Logs: Airflow, Jupyter, MinIO, and PHP all emitted normal startup lines; scheduler logs only reflected the base heartbeat DAGs.

#### Result
fail

#### Evidence
- Commands run:
  - `bash overlay_asx_historic_csv/dev-start-compose.sh`
  - `docker compose -f docker-compose.yaml -f overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml ps`
  - `curl -fsS http://localhost:8080/health`
  - `docker compose -f docker-compose.yaml -f overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml exec -T airflow-webserver airflow dags list`
  - `docker compose -f docker-compose.yaml -f overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml exec -T airflow-webserver python -c "...urllib..."`
  - `docker compose -f docker-compose.yaml -f overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml exec -T airflow-webserver python -c "...boto3..."`
  - `bash overlay_asx_historic_csv/dev-stop-compose.sh`
- Key log excerpts:
  - `asx200_ohlcv_daily_to_raw | /opt/airflow/dags/asx200_ohlcv_daily_to_raw.py`
  - `heartbeat_1m_to_raw | /opt/airflow/dags/heartbeat_1m_to_raw.py`
  - no `dag_asx_historic_csv` entry in the Airflow DAG list
  - `"raw_asx_historic_example": []`

### overlay_kaggle_ingestion

#### Command
`bash overlay_kaggle_ingestion/dev-start-compose.sh`

#### Start Result
success

#### Observations
- Container status: all base services reached `Up`, and the Airflow webserver became healthy.
- UI reachability:
  - Airflow health returned 200 from `http://localhost:8080/health`.
  - Jupyter login returned 200 from `http://jupyter:8888/login` via in-network probe.
  - PHP page returned 200 from `http://php/solutions/dataset_summary.php` via in-network probe.
  - MinIO API and console returned 200 via in-network probe.
- DAG visibility: declared DAG `dag_kaggle_ingestion` was not present in `airflow dags list`.
- Object-store evidence: buckets `raw`, `conformed`, and `curated` existed; the documented `kaggle/stroke_prediction` prefixes were empty.
- Logs: Airflow, Jupyter, MinIO, and PHP all emitted normal startup lines; scheduler activity again reflected only the base heartbeat DAGs.

#### Result
fail

#### Evidence
- Commands run:
  - `bash overlay_kaggle_ingestion/dev-start-compose.sh`
  - `docker compose -f docker-compose.yaml -f overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml ps`
  - `curl -fsS http://localhost:8080/health`
  - `docker compose -f docker-compose.yaml -f overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml exec -T airflow-webserver airflow dags list`
  - `docker compose -f docker-compose.yaml -f overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml exec -T airflow-webserver python -c "...urllib..."`
  - `docker compose -f docker-compose.yaml -f overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml exec -T airflow-webserver python -c "...boto3..."`
  - `bash overlay_kaggle_ingestion/dev-stop-compose.sh`
- Key log excerpts:
  - `asx200_ohlcv_daily_to_raw | /opt/airflow/dags/asx200_ohlcv_daily_to_raw.py`
  - `heartbeat_1m_to_raw | /opt/airflow/dags/heartbeat_1m_to_raw.py`
  - no `dag_kaggle_ingestion` entry in the Airflow DAG list
  - `"raw_kaggle_stroke_prediction": []`

### overlay_file_only_demo

#### Command
`./start-compose.sh`

#### Start Result
success

#### Observations
- Container status: all base services reached `Up`, and the Airflow webserver became healthy.
- UI reachability:
  - Airflow health returned 200 from `http://localhost:8080/health`.
  - Jupyter login returned 200 from `http://jupyter:8888/login` via in-network probe.
  - PHP page returned 200 from `http://php/solutions/file_only_demo.php` via in-network probe.
  - MinIO API and console returned 200 via in-network probe.
- DAG visibility: no overlay DAG is declared for this overlay.
- Object-store evidence: no overlay object-store surface is declared for this overlay.
- Logs: base services started normally; scheduler activity reflected only the base heartbeat DAGs.

#### Result
pass

#### Evidence
- Commands run:
  - `./start-compose.sh`
  - `docker compose -f docker-compose.yaml ps`
  - `curl -fsS http://localhost:8080/health`
  - `docker compose -f docker-compose.yaml exec -T airflow-webserver python -c "...urllib..."`
  - `./stop-compose.sh`
- Key log excerpts:
  - `Stack is starting. Default access URLs...`
  - `"php_file_only_demo": {"status": 200, "content_type": "text/html; charset=UTF-8"}`

## Notes

- Validation used only the documented Community dev-mode commands from `docs/internal/ov_04_cross_repo_overlay_test_matrix.md`.
- Only one overlay stack was run at a time, and each successful start was followed by a repo-scoped shutdown before the next overlay.
- Direct host `curl` checks were reliable for Airflow on port `8080`, but host probes to `8888`, `8088`, `9000`, and `9001` were not reliable from this execution environment; Jupyter, PHP, and MinIO reachability was therefore verified from within the running Compose network using `airflow-webserver`.
