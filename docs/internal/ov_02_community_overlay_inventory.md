# OV-02 — Community Overlay Inventory

## Branch Verification
- Repository: Community
- Branch: `feature/rearchitecture-runtime-overlay-contract`
- Result: pass

## Discovery Scope
- Directories inspected: `overlay_hello_world/`, `overlay_heartbeat_v2/`, `overlay_asx_historic_csv/`, `overlay_kaggle_ingestion/`, `overlay_file_only_demo/`, `docs/internal/`, `docs/reference/`, `docs/architecture/`, `php/`, `config/`, `dags/`, `notebooks/`
- File patterns inspected: `README.md`, `RUNBOOK.md`, `*.yaml`, `*.sh`, `*.py`, `*.ipynb`, `*.php`, `*.json`, `Dockerfile`
- Search methods used: `git branch --show-current`, `rg --files`, `find`, `rg`, `sed`

## Overlay Summary Table

| overlay | path | purpose | dev_mode_command | archive_command | install_command | installed_start_command | declared_dags | declared_outputs | declared_notebooks | declared_php_ui | documentation_gaps | contract_concerns |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `overlay_hello_world` | `overlay_hello_world/` | Reference compose overlay with deterministic local sample -> raw -> conformed -> curated flow (`overlay_hello_world/docs/explanation.md`, `overlay_hello_world/overlay_hello_world/README.md`) | `bash overlay_hello_world/dev-start-compose.sh` (`overlay_hello_world/overlay_hello_world/README.md`, `overlay_hello_world/dev-start-compose.sh`) | `cd overlay_hello_world && zip -rq ../overlay_hello_world_v1.0.zip config scripts dags notebooks php data overlay_hello_world` (`overlay_hello_world/overlay_hello_world/README.md`) | `unzip -oq overlay_hello_world_v1.0.zip -d .` then `cp config/hello_world_job.example.json config/hello_world_job.json` (`overlay_hello_world/overlay_hello_world/README.md`) | `bash overlay_hello_world/start-compose.sh` (`overlay_hello_world/overlay_hello_world/README.md`) | `dag_hello_world` (`overlay_hello_world/dags/dag_hello_world.py`) | Local mirrors under `data/raw/hello_world`, `data/conformed/hello_world`, `data/curated/hello_world`; optional S3 writes to `raw`, `conformed`, `curated` (`overlay_hello_world/docs/explanation.md`, `overlay_hello_world/scripts/*.py`) | `overlay_hello_world/notebooks/hello_world_validation.ipynb` | `overlay_hello_world/php/solutions/hello_world_summary.php` | No overlay-root README in `overlay_hello_world/`; installed docs live under `overlay_hello_world/overlay_hello_world/` | No logical `airflow` reference found; compose targets `airflow-webserver` and `airflow-scheduler`; optional S3 writes depend on base/env-provided credentials not overlay compose |
| `overlay_heartbeat_v2` | `overlay_heartbeat_v2/` | Additive heartbeat overlay that recreates the base heartbeat flow with `heartbeat_v2/` prefixes (`overlay_heartbeat_v2/overlay_heartbeat_v2/README.md`) | `bash overlay_heartbeat_v2/dev-start-compose.sh` (`overlay_heartbeat_v2/overlay_heartbeat_v2/README.md`, `overlay_heartbeat_v2/dev-start-compose.sh`) | `cd overlay_heartbeat_v2 && zip -rq ../overlay_heartbeat_v2.zip dags notebooks overlay_heartbeat_v2` (`overlay_heartbeat_v2/overlay_heartbeat_v2/RUNBOOK.md`) | `unzip -oq overlay_heartbeat_v2.zip -d .` (`overlay_heartbeat_v2/overlay_heartbeat_v2/README.md`) | `bash overlay_heartbeat_v2/start-compose.sh` (`overlay_heartbeat_v2/overlay_heartbeat_v2/README.md`) | `heartbeat_v2_to_raw`, `heartbeat_v2_copy_raw_to_conformed`, `heartbeat_v2_copy_conformed_to_curated` (`overlay_heartbeat_v2/dags/*.py`) | `raw/heartbeat_v2/...`, `conformed/heartbeat_v2/...`, `curated/heartbeat_v2/...` (`overlay_heartbeat_v2/overlay_heartbeat_v2/README.md`, `overlay_heartbeat_v2/dags/*.py`) | `overlay_heartbeat_v2/notebooks/heartbeat_v2_validation.ipynb` | `NONE DECLARED` | No packaged compose file; archive naming omits version suffix unlike other overlays; installed wrapper just delegates to root `start-compose.sh`/`stop-compose.sh` | Dev compose targets `airflow-webserver` and `airflow-scheduler`; installed mode relies on additive unzip into base mount surfaces; DAG code uses fallback MinIO credentials and endpoint defaults |
| `overlay_asx_historic_csv` | `overlay_asx_historic_csv/` | Compose overlay for HTTP/HTTPS CSV/XLS/XLSX ingestion to raw/conformed/curated with local PHP summary mirror (`overlay_asx_historic_csv/overlay_asx_historic_csv/README.md`, `overlay_asx_historic_csv/docs/explanation.md`) | `bash overlay_asx_historic_csv/dev-start-compose.sh` (`overlay_asx_historic_csv/overlay_asx_historic_csv/README.md`, `overlay_asx_historic_csv/dev-start-compose.sh`) | `cd overlay_asx_historic_csv && zip -rq ../overlay_asx_historic_csv_v1.0.zip config scripts dags notebooks php overlay_asx_historic_csv` (`overlay_asx_historic_csv/overlay_asx_historic_csv/README.md`) | `unzip -oq overlay_asx_historic_csv_v1.0.zip -d .` then `cp config/asx_historic_jobs.example.json config/asx_historic_jobs.json` (`overlay_asx_historic_csv/overlay_asx_historic_csv/README.md`) | `bash overlay_asx_historic_csv/start-compose.sh` (`overlay_asx_historic_csv/overlay_asx_historic_csv/README.md`) | `dag_asx_historic_csv` (`overlay_asx_historic_csv/dags/dag_asx_historic_csv.py`) | Raw prefix, conformed parquet target, curated JSON target from `config/asx_historic_jobs*.json`; MinIO buckets default to `raw`, `conformed`, `curated`; curated JSON mirrored under `data/curated/asx/historic/...` (`overlay_asx_historic_csv/config/asx_historic_jobs.example.json`, `overlay_asx_historic_csv/scripts/*.py`, `overlay_asx_historic_csv/php/solutions/asx_historic_summary.php`) | `overlay_asx_historic_csv/notebooks/asx_historic_connectivity_and_eda.ipynb` | `overlay_asx_historic_csv/php/solutions/asx_historic_summary.php` | `docs/article_outline.md` references test config files not present in repo; packaged compose mounts repo-root `./scripts`, `./data`, `./config` rather than overlay-scoped paths | No logical `airflow` reference found; compose targets `airflow-webserver` and `airflow-scheduler`; scripts use fallback MinIO credentials and undeclared env knobs such as `ASX_*`, `OPEN_DATA_LAKE_REPO_ROOT` |
| `overlay_kaggle_ingestion` | `overlay_kaggle_ingestion/` | Compose overlay for Kaggle CSV ingestion to raw/conformed/curated with PHP summary mirror (`overlay_kaggle_ingestion/README.md`, `overlay_kaggle_ingestion/docs/explanation.md`) | `bash overlay_kaggle_ingestion/dev-start-compose.sh` (`overlay_kaggle_ingestion/README.md`, `overlay_kaggle_ingestion/dev-start-compose.sh`) | `cd overlay_kaggle_ingestion && zip -rq ../overlay_kaggle_ingestion_v1.0.zip config scripts dags notebooks php overlay_kaggle_ingestion` (`overlay_kaggle_ingestion/overlay_kaggle_ingestion/README.md`, `overlay_kaggle_ingestion/overlay_kaggle_ingestion/RUNBOOK.md`) | `unzip -oq overlay_kaggle_ingestion_v1.0.zip -d .` then `cp config/kaggle_jobs.example.json config/kaggle_jobs.json` (`overlay_kaggle_ingestion/README.md`, `overlay_kaggle_ingestion/overlay_kaggle_ingestion/README.md`) | `bash overlay_kaggle_ingestion/start-compose.sh` (`overlay_kaggle_ingestion/README.md`, `overlay_kaggle_ingestion/overlay_kaggle_ingestion/README.md`) | `dag_kaggle_ingestion` (`overlay_kaggle_ingestion/dags/dag_kaggle_ingestion.py`) | Raw prefix, conformed parquet target, curated JSON target from `config/kaggle_jobs*.json`; MinIO buckets default to `raw`, `conformed`, `curated`; curated JSON mirrored under `data/curated/kaggle/...` (`overlay_kaggle_ingestion/config/kaggle_jobs.example.json`, `overlay_kaggle_ingestion/scripts/*.py`, `overlay_kaggle_ingestion/php/solutions/dataset_summary.php`) | `overlay_kaggle_ingestion/notebooks/kaggle_connectivity_and_eda.ipynb` | `overlay_kaggle_ingestion/php/solutions/dataset_summary.php` | Archive command differs between top-level README (`zip -rq ../overlay_kaggle_ingestion_v1.0.zip .`) and packaged docs (explicit file list); packaged compose mounts repo-root `./scripts`, `./data`, `./config` rather than overlay-scoped paths | No logical `airflow` reference found; compose targets `airflow-webserver` and `airflow-scheduler`; scripts use fallback MinIO credentials and require undeclared Kaggle/env knobs such as `KAGGLE_*`, `KAGGLE_JOBS_CONFIG`, `OPEN_DATA_LAKE_REPO_ROOT` |
| `overlay_file_only_demo` | `overlay_file_only_demo/` | Minimal file-only overlay that adds one PHP solution page without compose changes (`overlay_file_only_demo/overlay_file_only_demo/README.md`) | `./start-compose.sh` (`overlay_file_only_demo/overlay_file_only_demo/README.md`, `overlay_file_only_demo/overlay_file_only_demo/RUNBOOK.md`) | `cd overlay_file_only_demo && zip -rq ../overlay_file_only_demo_v1.0.zip php overlay_file_only_demo` (`overlay_file_only_demo/overlay_file_only_demo/README.md`) | `unzip -oq overlay_file_only_demo_v1.0.zip -d .` (`overlay_file_only_demo/overlay_file_only_demo/README.md`) | `./start-compose.sh` (`overlay_file_only_demo/overlay_file_only_demo/README.md`) | `NONE DECLARED` | `NONE DECLARED` | `NONE DECLARED` | `overlay_file_only_demo/php/solutions/file_only_demo.php` | No source-tree wrapper by design; no tagged solution metadata, so listing behavior depends on base PHP discovery logic | No logical `airflow` reference; no `airflow-webserver` or `airflow-scheduler` targets because this is intentionally file-only |

## Overlay Detail Sections

### overlay_hello_world

#### Location
- `overlay_hello_world/`

#### Evidence Files
- `overlay_hello_world/overlay_hello_world/README.md`
- `overlay_hello_world/overlay_hello_world/RUNBOOK.md`
- `overlay_hello_world/dev-start-compose.sh`
- `overlay_hello_world/dev-docker-compose.overlay-hello-world.yaml`
- `overlay_hello_world/overlay_hello_world/start-compose.sh`
- `overlay_hello_world/overlay_hello_world/docker-compose.overlay-hello-world.yaml`
- `overlay_hello_world/dags/dag_hello_world.py`
- `overlay_hello_world/scripts/hello_world_common.py`
- `overlay_hello_world/scripts/hello_world_local_to_raw.py`
- `overlay_hello_world/scripts/hello_world_raw_to_conformed.py`
- `overlay_hello_world/scripts/hello_world_conformed_to_curated.py`
- `overlay_hello_world/notebooks/hello_world_validation.ipynb`
- `overlay_hello_world/php/solutions/hello_world_summary.php`
- `overlay_hello_world/config/hello_world_job.example.json`
- `overlay_hello_world/docs/explanation.md`

#### Declared Commands
- Dev mode startup: `bash overlay_hello_world/dev-start-compose.sh`
- Archive/package generation: `cd overlay_hello_world && zip -rq ../overlay_hello_world_v1.0.zip config scripts dags notebooks php data overlay_hello_world`
- Installed/package installation: `unzip -oq overlay_hello_world_v1.0.zip -d .` then `cp config/hello_world_job.example.json config/hello_world_job.json`
- Installed/package startup: `bash overlay_hello_world/start-compose.sh`

#### Declared Runtime Surfaces
- DAGs: `dag_hello_world` with tasks `local_sample_to_raw`, `raw_to_conformed`, `conformed_to_curated`
- Object-store writes: config declares `raw_bucket=raw`, `raw_key=hello_world/raw/records.json`, `conformed_bucket=conformed`, `conformed_key=hello_world/conformed/records.json`, `curated_bucket=curated`, `curated_key=hello_world/curated/latest/summary.json`; scripts also write local mirrors under `data/raw/hello_world/records.json`, `data/conformed/hello_world/records.json`, `data/curated/hello_world/latest/summary.json`
- Notebooks: `overlay_hello_world/notebooks/hello_world_validation.ipynb`
- PHP/UI assets: `overlay_hello_world/php/solutions/hello_world_summary.php`
- Config files: `overlay_hello_world/config/hello_world_job.example.json`, `overlay_hello_world/overlay_hello_world/.env.example`
- Scripts: `overlay_hello_world/scripts/hello_world_common.py`, `hello_world_local_to_raw.py`, `hello_world_raw_to_conformed.py`, `hello_world_conformed_to_curated.py`
- Environment variables: `HELLO_WORLD_CONFIG_DIR`, `HELLO_WORLD_LOCAL_DATA_DIR`, `HELLO_WORLD_SAMPLE_DIR`, optional `S3_ENDPOINT_URL` or `S3_ENDPOINT`, `AWS_ACCESS_KEY_ID` or `S3_ACCESS_KEY`, `AWS_SECRET_ACCESS_KEY` or `S3_SECRET_KEY`, `AWS_DEFAULT_REGION` or `S3_REGION`, `ENABLED_SOLUTION_TAGS`
- Base service dependencies: `airflow-webserver`, `airflow-scheduler`, `jupyter`, `php`; optional object-store connectivity through base-provided S3/MinIO environment

#### Contract Checks
- References logical `airflow`: no
- Targets `airflow-webserver`: yes
- Targets `airflow-scheduler`: yes
- Uses fallback credentials: no
- Depends on undeclared env values: yes

#### Documentation Gaps
- No overlay-root `overlay_hello_world/README.md`; the operator-facing docs are inside `overlay_hello_world/overlay_hello_world/`
- Docs describe optional object-store writes, but the compose layer does not declare the S3/AWS variables used by `hello_world_common.py`

#### Discovery Result
- pass

### overlay_heartbeat_v2

#### Location
- `overlay_heartbeat_v2/`

#### Evidence Files
- `overlay_heartbeat_v2/overlay_heartbeat_v2/README.md`
- `overlay_heartbeat_v2/overlay_heartbeat_v2/RUNBOOK.md`
- `overlay_heartbeat_v2/dev-start-compose.sh`
- `overlay_heartbeat_v2/dev-docker-compose.overlay-heartbeat-v2.yaml`
- `overlay_heartbeat_v2/overlay_heartbeat_v2/start-compose.sh`
- `overlay_heartbeat_v2/dags/dag_heartbeat_v2_to_raw.py`
- `overlay_heartbeat_v2/dags/dag_heartbeat_v2_copy_raw_to_conformed.py`
- `overlay_heartbeat_v2/dags/dag_heartbeat_v2_copy_conformed_to_curated.py`
- `overlay_heartbeat_v2/notebooks/heartbeat_v2_validation.ipynb`

#### Declared Commands
- Dev mode startup: `bash overlay_heartbeat_v2/dev-start-compose.sh`
- Archive/package generation: `cd overlay_heartbeat_v2 && zip -rq ../overlay_heartbeat_v2.zip dags notebooks overlay_heartbeat_v2`
- Installed/package installation: `unzip -oq overlay_heartbeat_v2.zip -d .`
- Installed/package startup: `bash overlay_heartbeat_v2/start-compose.sh`

#### Declared Runtime Surfaces
- DAGs: `heartbeat_v2_to_raw`, `heartbeat_v2_copy_raw_to_conformed`, `heartbeat_v2_copy_conformed_to_curated`
- Object-store writes: `raw/heartbeat_v2/...`, `conformed/heartbeat_v2/...`, `curated/heartbeat_v2/...`
- Notebooks: `overlay_heartbeat_v2/notebooks/heartbeat_v2_validation.ipynb`
- PHP/UI assets: `NONE DECLARED`
- Config files: `NONE DECLARED`
- Scripts: wrapper scripts only; transformation logic is in DAG files
- Environment variables: `S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION` in `dag_heartbeat_v2_to_raw.py`
- Base service dependencies: dev compose targets `airflow-webserver`, `airflow-scheduler`, `jupyter`; runtime object-store access depends on base MinIO/S3 endpoint and credentials

#### Contract Checks
- References logical `airflow`: no
- Targets `airflow-webserver`: yes
- Targets `airflow-scheduler`: yes
- Uses fallback credentials: yes
- Depends on undeclared env values: yes

#### Documentation Gaps
- No packaged `docker-compose.overlay-*.yaml`; installed wrapper does not pass `--overlay`, so installed behavior depends on additive unzip into base runtime mounts
- Archive name is `overlay_heartbeat_v2.zip`, unlike the version-suffixed archives used by other overlays
- No PHP/config surface is documented because none is present; validation surface is limited to DAGs, MinIO, and one notebook

#### Discovery Result
- pass

### overlay_asx_historic_csv

#### Location
- `overlay_asx_historic_csv/`

#### Evidence Files
- `overlay_asx_historic_csv/overlay_asx_historic_csv/README.md`
- `overlay_asx_historic_csv/overlay_asx_historic_csv/RUNBOOK.md`
- `overlay_asx_historic_csv/dev-start-compose.sh`
- `overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml`
- `overlay_asx_historic_csv/overlay_asx_historic_csv/start-compose.sh`
- `overlay_asx_historic_csv/overlay_asx_historic_csv/docker-compose.overlay-asx-historic-csv.yaml`
- `overlay_asx_historic_csv/config/asx_historic_jobs.example.json`
- `overlay_asx_historic_csv/dags/dag_asx_historic_csv.py`
- `overlay_asx_historic_csv/scripts/asx_overlay_common.py`
- `overlay_asx_historic_csv/scripts/asx_urls_to_raw.py`
- `overlay_asx_historic_csv/scripts/raw_to_conformed.py`
- `overlay_asx_historic_csv/scripts/conformed_to_curated.py`
- `overlay_asx_historic_csv/notebooks/asx_historic_connectivity_and_eda.ipynb`
- `overlay_asx_historic_csv/php/solutions/asx_historic_summary.php`
- `overlay_asx_historic_csv/docs/explanation.md`
- `overlay_asx_historic_csv/docs/article_outline.md`

#### Declared Commands
- Dev mode startup: `bash overlay_asx_historic_csv/dev-start-compose.sh`
- Archive/package generation: `cd overlay_asx_historic_csv && zip -rq ../overlay_asx_historic_csv_v1.0.zip config scripts dags notebooks php overlay_asx_historic_csv`
- Installed/package installation: `unzip -oq overlay_asx_historic_csv_v1.0.zip -d .` then `cp config/asx_historic_jobs.example.json config/asx_historic_jobs.json`
- Installed/package startup: `bash overlay_asx_historic_csv/start-compose.sh`

#### Declared Runtime Surfaces
- DAGs: `dag_asx_historic_csv` with tasks `asx_urls_to_raw`, `raw_to_conformed`, `conformed_to_curated`
- Object-store writes: example config declares `raw_target=asx/historic/example/`, `conformed_target=asx/historic/example/example.parquet`, `curated_target=asx/historic/example/example_summary.json`; scripts write to MinIO buckets `raw`, `conformed`, `curated` by default and mirror curated JSON under `data/curated/asx/historic/...`
- Notebooks: `overlay_asx_historic_csv/notebooks/asx_historic_connectivity_and_eda.ipynb`
- PHP/UI assets: `overlay_asx_historic_csv/php/solutions/asx_historic_summary.php`
- Config files: `overlay_asx_historic_csv/config/asx_historic_jobs.example.json`, `overlay_asx_historic_csv/.env.example`
- Scripts: `overlay_asx_historic_csv/scripts/asx_overlay_common.py`, `asx_urls_to_raw.py`, `raw_to_conformed.py`, `conformed_to_curated.py`
- Environment variables: `OPEN_DATA_LAKE_REPO_ROOT`, `ASX_HISTORIC_JOBS_CONFIG`, `ASX_HISTORIC_JOB_NAME`, `ASX_RAW_BUCKET`, `ASX_CONFORMED_BUCKET`, `ASX_CURATED_BUCKET`, `ASX_CURATED_LOCAL_ROOT`, `S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `MINIO_ROOT_USER`, `AWS_SECRET_ACCESS_KEY`, `MINIO_ROOT_PASSWORD`, `AWS_DEFAULT_REGION`, `ENABLED_SOLUTION_TAGS`
- Base service dependencies: `airflow-webserver`, `airflow-scheduler`, `jupyter`, `php`; HTTP/HTTPS source access in `asx_urls_to_raw.py`; base MinIO/S3 credentials

#### Contract Checks
- References logical `airflow`: no
- Targets `airflow-webserver`: yes
- Targets `airflow-scheduler`: yes
- Uses fallback credentials: yes
- Depends on undeclared env values: yes

#### Documentation Gaps
- `overlay_asx_historic_csv/docs/article_outline.md` references `config/asx_historic_jobs.test.json` and `config/asx_historic_jobs.marketindex_2016_2024.test.json`, but those files are not present
- Installed compose file mounts repo-root `./scripts`, `./data`, `./config`; the packaged docs do not explicitly call out that the overlay expects those shared runtime surfaces after unzip

#### Discovery Result
- pass

### overlay_kaggle_ingestion

#### Location
- `overlay_kaggle_ingestion/`

#### Evidence Files
- `overlay_kaggle_ingestion/README.md`
- `overlay_kaggle_ingestion/overlay_kaggle_ingestion/README.md`
- `overlay_kaggle_ingestion/overlay_kaggle_ingestion/RUNBOOK.md`
- `overlay_kaggle_ingestion/dev-start-compose.sh`
- `overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml`
- `overlay_kaggle_ingestion/overlay_kaggle_ingestion/start-compose.sh`
- `overlay_kaggle_ingestion/overlay_kaggle_ingestion/docker-compose.overlay-kaggle.yaml`
- `overlay_kaggle_ingestion/config/kaggle_jobs.example.json`
- `overlay_kaggle_ingestion/dags/dag_kaggle_ingestion.py`
- `overlay_kaggle_ingestion/scripts/kaggle_overlay_common.py`
- `overlay_kaggle_ingestion/scripts/kaggle_to_raw.py`
- `overlay_kaggle_ingestion/scripts/raw_to_conformed.py`
- `overlay_kaggle_ingestion/scripts/conformed_to_curated.py`
- `overlay_kaggle_ingestion/notebooks/kaggle_connectivity_and_eda.ipynb`
- `overlay_kaggle_ingestion/php/solutions/dataset_summary.php`
- `overlay_kaggle_ingestion/docs/explanation.md`

#### Declared Commands
- Dev mode startup: `bash overlay_kaggle_ingestion/dev-start-compose.sh`
- Archive/package generation: `cd overlay_kaggle_ingestion && zip -rq ../overlay_kaggle_ingestion_v1.0.zip config scripts dags notebooks php overlay_kaggle_ingestion`
- Installed/package installation: `unzip -oq overlay_kaggle_ingestion_v1.0.zip -d .` then `cp config/kaggle_jobs.example.json config/kaggle_jobs.json`
- Installed/package startup: `bash overlay_kaggle_ingestion/start-compose.sh`

#### Declared Runtime Surfaces
- DAGs: `dag_kaggle_ingestion` with tasks `kaggle_to_raw`, `raw_to_conformed`, `conformed_to_curated`
- Object-store writes: example config declares `raw_target=kaggle/stroke_prediction`, `conformed_target=kaggle/stroke_prediction/stroke_prediction.parquet`, `curated_target=kaggle/stroke_prediction/stroke_prediction_summary.json`; scripts write to MinIO buckets `raw`, `conformed`, `curated` by default and mirror curated JSON under `data/curated/kaggle/...`
- Notebooks: `overlay_kaggle_ingestion/notebooks/kaggle_connectivity_and_eda.ipynb`
- PHP/UI assets: `overlay_kaggle_ingestion/php/solutions/dataset_summary.php`
- Config files: `overlay_kaggle_ingestion/config/kaggle_jobs.example.json`, `overlay_kaggle_ingestion/.env.example`
- Scripts: `overlay_kaggle_ingestion/scripts/kaggle_overlay_common.py`, `kaggle_to_raw.py`, `raw_to_conformed.py`, `conformed_to_curated.py`
- Environment variables: `OPEN_DATA_LAKE_REPO_ROOT`, `KAGGLE_JOBS_CONFIG`, `KAGGLE_JOB_NAME`, `KAGGLE_API_TOKEN`, `KAGGLE_USERNAME`, `KAGGLE_KEY`, `KAGGLE_CONFIG_DIR`, `KAGGLE_RAW_BUCKET`, `KAGGLE_CONFORMED_BUCKET`, `KAGGLE_CURATED_BUCKET`, `KAGGLE_CURATED_SUMMARY_PATH`, `S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `MINIO_ROOT_USER`, `AWS_SECRET_ACCESS_KEY`, `MINIO_ROOT_PASSWORD`, `AWS_DEFAULT_REGION`, `ENABLED_SOLUTION_TAGS`
- Base service dependencies: `airflow-webserver`, `airflow-scheduler`, `jupyter`, `php`; Kaggle API access; base MinIO/S3 credentials

#### Contract Checks
- References logical `airflow`: no
- Targets `airflow-webserver`: yes
- Targets `airflow-scheduler`: yes
- Uses fallback credentials: yes
- Depends on undeclared env values: yes

#### Documentation Gaps
- Top-level `overlay_kaggle_ingestion/README.md` archive command (`zip -rq ../overlay_kaggle_ingestion_v1.0.zip .`) conflicts with packaged README/RUNBOOK explicit file list
- Installed compose file mounts repo-root `./scripts`, `./data`, `./config`; the packaged docs do not explicitly describe that shared-surface dependency in the same detail as the wrapper command

#### Discovery Result
- pass

### overlay_file_only_demo

#### Location
- `overlay_file_only_demo/`

#### Evidence Files
- `overlay_file_only_demo/overlay_file_only_demo/README.md`
- `overlay_file_only_demo/overlay_file_only_demo/RUNBOOK.md`
- `overlay_file_only_demo/php/solutions/file_only_demo.php`

#### Declared Commands
- Dev mode startup: `./start-compose.sh`
- Archive/package generation: `cd overlay_file_only_demo && zip -rq ../overlay_file_only_demo_v1.0.zip php overlay_file_only_demo`
- Installed/package installation: `unzip -oq overlay_file_only_demo_v1.0.zip -d .`
- Installed/package startup: `./start-compose.sh`

#### Declared Runtime Surfaces
- DAGs: `NONE DECLARED`
- Object-store writes: `NONE DECLARED`
- Notebooks: `NONE DECLARED`
- PHP/UI assets: `overlay_file_only_demo/php/solutions/file_only_demo.php`
- Config files: `NONE DECLARED`
- Scripts: `NONE DECLARED`
- Environment variables: `NONE DECLARED`
- Base service dependencies: base `php` service and base `./php` bind mount; runtime page requires `php/inc/submenu.php` and `php/inc/layout.php`

#### Contract Checks
- References logical `airflow`: no
- Targets `airflow-webserver`: no
- Targets `airflow-scheduler`: no
- Uses fallback credentials: no
- Depends on undeclared env values: no

#### Documentation Gaps
- No explicit note on whether the untagged PHP page will always appear in the Solutions UI or depends on base-page discovery logic

#### Discovery Result
- pass

## Cross-Cutting Findings
- Five overlays were discovered: four runtime/data overlays and one file-only PHP overlay.
- All compose-based overlays target `airflow-webserver` and `airflow-scheduler`; no overlay compose file references a logical `airflow` service.
- `overlay_heartbeat_v2` is structurally different from the other packaged overlays because installed mode relies on additive DAG/notebook placement rather than a packaged compose file.
- `overlay_asx_historic_csv` and `overlay_kaggle_ingestion` both mount repo-root shared runtime surfaces after unzip and both expose extra environment knobs that are not fully declared in overlay compose files.
- `overlay_heartbeat_v2`, `overlay_asx_historic_csv`, and `overlay_kaggle_ingestion` contain fallback MinIO credential defaults in discovery evidence.
- Documentation consistency gaps exist around archive naming/build commands and around referenced-but-missing test config files.

## Validation Not Performed
- Discovery only. No runtime validation was performed.
- Docker was not started.
- Validation tests were not run.

## Recommended Next Task
- OV-03 — Discover Supported overlays
