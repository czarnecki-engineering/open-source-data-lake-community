# OV-06 — Community Installed-Mode Overlay Validation

## Branch Verification
- Branch: `feature/rearchitecture-runtime-overlay-contract`
- Result: pass

## Validation Summary Table

| overlay | archive | install | start | surfaces | result | notes |
|---|---|---|---|---|---|---|
| `overlay_hello_world` | pass | pass | pass | pass | pass | Archive/unzip/start worked in an isolated compatible checkout; `dag_hello_world`, notebook, PHP page, and MinIO buckets were present. The documented `hello_world/` object prefixes were empty because no DAG was triggered. |
| `overlay_heartbeat_v2` | pass | pass | blocked | blocked | blocked | Installed wrapper exited immediately with `Error: Docker daemon is not running. Start Docker Desktop and try again.` This reproduces the known shared Docker precheck issue. |
| `overlay_asx_historic_csv` | pass | pass | pass | pass | pass | Archive/unzip/start worked in an isolated compatible checkout after copying the documented example config to `config/asx_historic_jobs.json`; DAG, notebook, PHP page, and MinIO buckets were present. The documented `asx/historic/example/` prefixes were empty because no DAG was triggered. |
| `overlay_kaggle_ingestion` | pass | pass | blocked | blocked | blocked | Archive and unzip succeeded, but the installed wrapper exited immediately with `Error: Docker daemon is not running. Start Docker Desktop and try again.` The repo still has conflicting documented archive commands. |
| `overlay_file_only_demo` | pass | pass | pass | pass | pass | Archive/unzip/base start worked in an isolated compatible checkout; the declared PHP page loaded and the base Airflow/Jupyter/MinIO surfaces were reachable. No overlay DAG, notebook, or object prefix is declared. |

## Detailed Results

### overlay_hello_world

#### Archive Command
`cd overlay_hello_world && zip -rq ../overlay_hello_world_v1.0.zip config scripts dags notebooks php data overlay_hello_world`

#### Archive Result
success

#### Install Command
`unzip -oq overlay_hello_world_v1.0.zip -d .`

#### Install Result
success

#### Start Command
`bash overlay_hello_world/start-compose.sh`

#### Start Result
success

#### Runtime Surface Checks
- Airflow: pass. Container-local `http://localhost:8080/health` returned healthy scheduler and metadatabase JSON.
- DAGs: pass. `dag_hello_world` was visible at `/opt/airflow/dags/dag_hello_world.py`.
- PHP/UI: pass. `http://php/solutions/hello_world_summary.php` returned `200 text/html`.
- Jupyter: pass. `http://jupyter:8888/login` returned `200 text/html`.
- Object store: pass. Buckets `raw`, `conformed`, and `curated` existed. `hello_world/` prefixes in all three buckets were empty because no DAG was triggered.

#### Result
pass

#### Evidence
- commands run:
  - `cd overlay_hello_world && zip -rq ../overlay_hello_world_v1.0.zip config scripts dags notebooks php data overlay_hello_world`
  - `unzip -oq overlay_hello_world_v1.0.zip -d .`
  - `bash overlay_hello_world/start-compose.sh`
  - `docker compose -f docker-compose.yaml -f overlay_hello_world/docker-compose.overlay-hello-world.yaml ps`
  - `docker compose -f docker-compose.yaml -f overlay_hello_world/docker-compose.overlay-hello-world.yaml exec -T airflow-webserver airflow dags list | rg 'dag_hello_world'`
  - `docker compose -f docker-compose.yaml -f overlay_hello_world/docker-compose.overlay-hello-world.yaml exec -T airflow-webserver python -c "...urllib.request.urlopen('http://localhost:8080/health')..."`
  - `docker compose -f docker-compose.yaml -f overlay_hello_world/docker-compose.overlay-hello-world.yaml exec -T airflow-webserver python -c "...urllib.request.urlopen('http://jupyter:8888/login')..."`
  - `docker compose -f docker-compose.yaml -f overlay_hello_world/docker-compose.overlay-hello-world.yaml exec -T airflow-webserver python -c "...urllib.request.urlopen('http://php/solutions/hello_world_summary.php')..."`
  - `docker compose -f docker-compose.yaml -f overlay_hello_world/docker-compose.overlay-hello-world.yaml exec -T airflow-webserver python -c "...boto3..."`
  - `docker compose down`
- key output excerpts:
  - `dag_hello_world | /opt/airflow/dags/dag_hello_world.py`
  - `200 text/html`
  - `{"buckets": ["conformed", "curated", "raw"], "raw_hello_world": [], "conformed_hello_world": [], "curated_hello_world": []}`

### overlay_heartbeat_v2

#### Archive Command
`cd overlay_heartbeat_v2 && zip -rq ../overlay_heartbeat_v2.zip dags notebooks overlay_heartbeat_v2`

#### Archive Result
success

#### Install Command
`unzip -oq overlay_heartbeat_v2.zip -d .`

#### Install Result
success

#### Start Command
`bash overlay_heartbeat_v2/start-compose.sh`

#### Start Result
blocked

#### Runtime Surface Checks
- Airflow: blocked before startup.
- DAGs: blocked before startup.
- PHP/UI: not declared.
- Jupyter: blocked before startup.
- Object store: blocked before startup.

#### Result
blocked

#### Evidence
- commands run:
  - `cd overlay_heartbeat_v2 && zip -rq ../overlay_heartbeat_v2.zip dags notebooks overlay_heartbeat_v2`
  - `unzip -oq overlay_heartbeat_v2.zip -d .`
  - `bash overlay_heartbeat_v2/start-compose.sh`
- key output excerpts:
  - `Error: Docker daemon is not running. Start Docker Desktop and try again.`

### overlay_asx_historic_csv

#### Archive Command
`cd overlay_asx_historic_csv && zip -rq ../overlay_asx_historic_csv_v1.0.zip config scripts dags notebooks php overlay_asx_historic_csv`

#### Archive Result
success

#### Install Command
`unzip -oq overlay_asx_historic_csv_v1.0.zip -d .`
`cp config/asx_historic_jobs.example.json config/asx_historic_jobs.json`

#### Install Result
success

#### Start Command
`bash overlay_asx_historic_csv/start-compose.sh`

#### Start Result
success

#### Runtime Surface Checks
- Airflow: pass. The first health probe hit `Connection refused` while the container was still `health: starting`; after a short wait the webserver became healthy and `http://localhost:8080/health` returned healthy scheduler and metadatabase JSON.
- DAGs: pass. `dag_asx_historic_csv` was visible at `/opt/airflow/dags/dag_asx_historic_csv.py`.
- PHP/UI: pass. `http://php/solutions/asx_historic_summary.php` returned `200 text/html`.
- Jupyter: pass. `http://jupyter:8888/login` returned `200 text/html`.
- Object store: pass. Buckets `raw`, `conformed`, and `curated` existed. The documented `asx/historic/example/` prefixes in all three buckets were empty because no DAG was triggered.

#### Result
pass

#### Evidence
- commands run:
  - `cd overlay_asx_historic_csv && zip -rq ../overlay_asx_historic_csv_v1.0.zip config scripts dags notebooks php overlay_asx_historic_csv`
  - `unzip -oq overlay_asx_historic_csv_v1.0.zip -d .`
  - `cp config/asx_historic_jobs.example.json config/asx_historic_jobs.json`
  - `bash overlay_asx_historic_csv/start-compose.sh`
  - `docker compose -f docker-compose.yaml -f overlay_asx_historic_csv/docker-compose.overlay-asx-historic-csv.yaml ps`
  - `docker compose -f docker-compose.yaml -f overlay_asx_historic_csv/docker-compose.overlay-asx-historic-csv.yaml exec -T airflow-webserver airflow dags list | rg 'dag_asx_historic_csv'`
  - `sleep 20`
  - `docker compose -f docker-compose.yaml -f overlay_asx_historic_csv/docker-compose.overlay-asx-historic-csv.yaml exec -T airflow-webserver python -c "...urllib.request.urlopen('http://localhost:8080/health')..."`
  - `docker compose -f docker-compose.yaml -f overlay_asx_historic_csv/docker-compose.overlay-asx-historic-csv.yaml exec -T airflow-webserver python -c "...urllib.request.urlopen('http://jupyter:8888/login')..."`
  - `docker compose -f docker-compose.yaml -f overlay_asx_historic_csv/docker-compose.overlay-asx-historic-csv.yaml exec -T airflow-webserver python -c "...urllib.request.urlopen('http://php/solutions/asx_historic_summary.php')..."`
  - `docker compose -f docker-compose.yaml -f overlay_asx_historic_csv/docker-compose.overlay-asx-historic-csv.yaml exec -T airflow-webserver python -c "...boto3..."`
  - `docker compose down`
- key output excerpts:
  - `dag_asx_historic_csv | /opt/airflow/dags/dag_asx_historic_csv.py`
  - `200 text/html`
  - `{"buckets": ["conformed", "curated", "raw"], "raw_asx_historic_example": [], "conformed_asx_historic_example": [], "curated_asx_historic_example": []}`
  - `Connection refused` on the initial Airflow health probe while `airflow-webserver` was still `health: starting`
  - `{"dag_processor": {"latest_dag_processor_heartbeat": null, "status": null}, "metadatabase": {"status": "healthy"}, "scheduler": {"latest_scheduler_heartbeat": "...", "status": "healthy"}, "triggerer": {"latest_triggerer_heartbeat": null, "status": null}}`

### overlay_kaggle_ingestion

#### Archive Command
`cd overlay_kaggle_ingestion && zip -rq ../overlay_kaggle_ingestion_v1.0.zip config scripts dags notebooks php overlay_kaggle_ingestion`

#### Archive Result
success

#### Install Command
`unzip -oq overlay_kaggle_ingestion_v1.0.zip -d .`
`cp config/kaggle_jobs.example.json config/kaggle_jobs.json`

#### Install Result
success

#### Start Command
`./overlay_kaggle_ingestion/start-compose.sh`

#### Start Result
blocked

#### Runtime Surface Checks
- Airflow: blocked before startup.
- DAGs: blocked before startup.
- PHP/UI: blocked before startup.
- Jupyter: blocked before startup.
- Object store: blocked before startup.

#### Result
blocked

#### Evidence
- commands run:
  - `cd overlay_kaggle_ingestion && zip -rq ../overlay_kaggle_ingestion_v1.0.zip config scripts dags notebooks php overlay_kaggle_ingestion`
  - `unzip -oq overlay_kaggle_ingestion_v1.0.zip -d .`
  - `cp config/kaggle_jobs.example.json config/kaggle_jobs.json`
  - `./overlay_kaggle_ingestion/start-compose.sh`
  - `docker info --format '{{.ServerVersion}}'`
- key output excerpts:
  - `Resolved overlays (merge order):`
  - `- overlay_kaggle_ingestion/docker-compose.overlay-kaggle.yaml`
  - `Error: Docker daemon is not running. Start Docker Desktop and try again.`
  - `29.1.2`

### overlay_file_only_demo

#### Archive Command
`cd overlay_file_only_demo && zip -rq ../overlay_file_only_demo_v1.0.zip php overlay_file_only_demo`

#### Archive Result
success

#### Install Command
`unzip -oq overlay_file_only_demo_v1.0.zip -d .`

#### Install Result
success

#### Start Command
`./start-compose.sh`

#### Start Result
success

#### Runtime Surface Checks
- Airflow: pass. The first health probe hit `Connection refused` while the container was still `health: starting`; after a short wait the webserver became healthy and `http://localhost:8080/health` returned healthy scheduler and metadatabase JSON.
- DAGs: not declared.
- PHP/UI: pass. `http://php/solutions/file_only_demo.php` returned `200 text/html`.
- Jupyter: pass. `http://jupyter:8888/login` returned `200 text/html`.
- Object store: pass. Buckets `raw`, `conformed`, and `curated` existed. No overlay-specific object path is declared.

#### Result
pass

#### Evidence
- commands run:
  - `cd overlay_file_only_demo && zip -rq ../overlay_file_only_demo_v1.0.zip php overlay_file_only_demo`
  - `unzip -oq overlay_file_only_demo_v1.0.zip -d .`
  - `./start-compose.sh`
  - `docker compose -f docker-compose.yaml ps`
  - `sleep 20`
  - `docker compose -f docker-compose.yaml exec -T airflow-webserver python -c "...urllib.request.urlopen('http://localhost:8080/health')..."`
  - `docker compose -f docker-compose.yaml exec -T airflow-webserver python -c "...urllib.request.urlopen('http://jupyter:8888/login')..."`
  - `docker compose -f docker-compose.yaml exec -T airflow-webserver python -c "...urllib.request.urlopen('http://php/solutions/file_only_demo.php')..."`
  - `docker compose -f docker-compose.yaml exec -T airflow-webserver python -c "...boto3..."`
  - `docker compose down`
- key output excerpts:
  - `200 text/html`
  - `{"buckets": ["conformed", "curated", "raw"]}`
  - `Connection refused` on the initial Airflow health probe while `airflow-webserver` was still `health: starting`
  - `{"dag_processor": {"latest_dag_processor_heartbeat": null, "status": null}, "metadatabase": {"status": "healthy"}, "scheduler": {"latest_scheduler_heartbeat": "...", "status": "healthy"}, "triggerer": {"latest_triggerer_heartbeat": null, "status": null}}`

## Cross-Cutting Findings

- Packaging consistency: `overlay_hello_world`, `overlay_asx_historic_csv`, and `overlay_file_only_demo` built archives that installed and started successfully in isolated compatible checkouts. `overlay_heartbeat_v2` still uses a non-versioned archive name, unlike the other packaged overlays.
- Archive completeness: the installed payloads for hello world, ASX historic CSV, and file-only demo were sufficient to restore the declared runtime surfaces after `unzip -oq ... -d .`.
- Install behaviour vs dev-mode: hello world, ASX historic CSV, and file-only demo remained stable in installed mode, matching the broad dev-mode outcome from OV-05D. Heartbeat remained blocked by the same startup precheck family. Kaggle diverged from OV-05D by blocking during installed-wrapper startup even though dev-mode had passed in OV-05D.
- Repeated documentation gaps: Kaggle still has conflicting archive commands between the top-level README and the packaged installed-mode docs. Heartbeat still documents installed mode without a packaged overlay compose file because its wrapper just delegates to the base `start-compose.sh`.
- Docker preflight issues: `overlay_heartbeat_v2` and `overlay_kaggle_ingestion` both failed at the same documented `Docker daemon is not running` precheck message before the stack started. Kaggle reproduced the message even though a direct `docker info --format '{{.ServerVersion}}'` in the same temp checkout returned `29.1.2`.
- Env dependency issues: no overlay was blocked by `.env` validation in this run. ASX and Kaggle both require copied example config files for installed mode; only ASX progressed far enough to validate the running surfaces. Kaggle credential requirements remained untested because startup blocked earlier.
- Runtime observation detail: ASX historic CSV and file-only demo both required a short wait before the Airflow webserver became healthy; their first health probes returned `Connection refused` while `airflow-webserver` was still `health: starting`.
- Validation isolation: the documented archive, install, and start commands were executed verbatim in isolated compatible temp checkouts under `/tmp/ov06.1pY0Ch/` so the working branch runtime files were not altered.

## Validation Not Performed

- No DAGs were triggered for any overlay because this task was limited to archive/install/start validation plus passive surface checks.
- Hello world, ASX historic CSV, and file-only demo object-prefix checks were limited to bucket/prefix visibility; the overlay-specific prefixes stayed empty because no DAG was triggered.
- Heartbeat v2 runtime surface checks were not performed because startup was blocked by the known Docker precheck issue.
- Kaggle runtime surface checks were not performed because startup was blocked by the same Docker precheck issue before any containers were created.
- Kaggle credential-dependent ingestion was not exercised because startup blocked before runtime validation.

## Recommended Next Task

OV-07 — Supported dev-mode overlay validation
