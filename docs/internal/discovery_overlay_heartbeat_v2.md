# Discovery: `overlay_heartbeat_v2`

## Executive summary

The current Community base heartbeat implementation is a set of three separate Airflow DAGs in `dags/`, not a single DAG:

- `dags/heartbeat_1m_to_raw.py`
- `dags/heartbeat_1m_copy_raw_to_conformed.py`
- `dags/heartbeat_1m_copy_conformed_to_curated.py`

Together they create a simple health-signal pipeline that writes timestamp text files into MinIO bucket `raw` under prefix `heartbeat/`, then copies the same objects into `conformed`, then copies them again into `curated`.

Repository evidence indicates the heartbeat DAGs are intended to auto-run by default:

- the three heartbeat DAGs are scheduled every minute
- all three have `catchup=False`
- the base Airflow environment sets `AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: "False"` in `docker-compose.yaml`
- `README.md` explicitly states: "Heartbeat DAGs run automatically and provide the system health signal."

No heartbeat-specific config file, PHP page, or packaged overlay currently exists in the repository. There is one notebook, `notebooks/read_heartbeat.ipynb`, which reads heartbeat files from MinIO `raw`.

If `overlay_heartbeat_v2` is added while the base heartbeat DAGs remain present and scheduled, the repo would have duplicate scheduled heartbeat workflows unless DAG IDs, schedules, or output prefixes are changed.

## Existing heartbeat implementation

### Source files

Confirmed heartbeat-specific implementation files:

- `dags/heartbeat_1m_to_raw.py`
- `dags/heartbeat_1m_copy_raw_to_conformed.py`
- `dags/heartbeat_1m_copy_conformed_to_curated.py`
- `notebooks/read_heartbeat.ipynb`

Secondary repo references to heartbeat behavior:

- `README.md`
- `config/README.md`
- `docs/reference/IMPLEMENTED_CAPABILITIES.md`
- `docs/reference/CONTENTS.md`
- `docs/internal/PROJECT_CONTEXT.md`

### Base workflow shape

The implementation is split across three independent minute-scheduled DAGs:

1. `heartbeat_1m_to_raw`
2. `heartbeat_1m_copy_raw_to_conformed`
3. `heartbeat_1m_copy_conformed_to_curated`

They are not defined as one DAG with downstream tasks. Instead, each DAG scans/copies based on object presence in MinIO.

### Relevant snippets

From `dags/heartbeat_1m_to_raw.py`:

```python
body = now.strftime("%Y-%m-%d %H:%M:%S %Z\n").encode()
key = f"heartbeat/airflow_time_{now.strftime('%Y%m%d_%H%M%S')}.txt"
s3.put_object(Bucket="raw", Key=key, Body=body)
```

From `dags/heartbeat_1m_copy_raw_to_conformed.py`:

```python
raw_objects = s3.list_objects_v2(Bucket=RAW_BUCKET, Prefix=PREFIX).get("Contents", [])
conformed_objects = s3.list_objects_v2(Bucket=CONFORMED_BUCKET, Prefix=PREFIX).get("Contents", [])
...
s3.copy_object(
    Bucket=CONFORMED_BUCKET,
    Key=key,
    CopySource={"Bucket": RAW_BUCKET, "Key": key},
)
```

From `dags/heartbeat_1m_copy_conformed_to_curated.py`:

```python
conformed_objects = s3.list_objects_v2(Bucket=CONFORMED_BUCKET, Prefix=PREFIX).get("Contents", [])
curated_objects = s3.list_objects_v2(Bucket=CURATED_BUCKET, Prefix=PREFIX).get("Contents", [])
...
s3.copy_object(
    Bucket=CURATED_BUCKET,
    Key=key,
    CopySource={"Bucket": CONFORMED_BUCKET, "Key": key},
)
```

## Triggering and schedule behaviour

### Confirmed triggering model

Confirmed from repository inspection:

- the heartbeat DAGs are scheduled automatically by Airflow
- they are not manual-trigger-only DAGs
- they are intended to auto-run by default in the base stack

Evidence:

- `README.md`: "Heartbeat DAGs run automatically and provide the system health signal."
- `docker-compose.yaml`: `AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: "False"`
- each heartbeat DAG declares a one-minute schedule

### DAG-by-DAG schedule details

#### `dags/heartbeat_1m_to_raw.py`

- `dag_id`: `heartbeat_1m_to_raw`
- task id: `write_time_to_raw`
- `start_date`: `pendulum.datetime(2024, 1, 1, tz="Australia/Melbourne")`
- `schedule`: `"* * * * *"`
- `catchup`: `False`
- `max_active_runs`: `1`
- `tags`: `["raw", "minio"]`
- `default_args`: none declared in file

#### `dags/heartbeat_1m_copy_raw_to_conformed.py`

- `dag_id`: `heartbeat_1m_copy_raw_to_conformed`
- task id: `copy_new_raw_objects`
- `start_date`: `datetime(2024, 1, 1)`
- `schedule_interval`: `"*/1 * * * *"`
- `catchup`: `False`
- `max_active_runs`: not declared
- `tags`: `["minio", "raw", "conformed"]`
- `default_args`:
  - `owner: airflow`
  - `retries: 0`

#### `dags/heartbeat_1m_copy_conformed_to_curated.py`

- `dag_id`: `heartbeat_1m_copy_conformed_to_curated`
- task id: `copy_new_conformed_objects`
- `start_date`: `datetime(2024, 1, 1)`
- `schedule_interval`: `"*/1 * * * *"`
- `catchup`: `False`
- `max_active_runs`: not declared
- `tags`: `["minio", "conformed", "curated"]`
- `default_args`: none declared in file

### Auto-run by default

Confirmed from repository inspection.

Why:

- the DAGs have schedules rather than `schedule=None`
- the base Airflow config does not pause new DAGs at creation
- repo docs define heartbeat DAG activity as the health signal for the platform

## Payload and output paths

### Generated data

The first DAG generates one plain text payload per run containing the current Melbourne time, formatted as:

```text
YYYY-MM-DD HH:MM:SS TZ
```

Confirmed formatter:

```python
now.strftime("%Y-%m-%d %H:%M:%S %Z\n")
```

Example recorded in `notebooks/read_heartbeat.ipynb` output:

```text
2025-12-16 21:02:15 AEDT
```

### Output format

- file format: plain text
- file extension: `.txt`
- content encoding: UTF-8 bytes via `.encode()`

### Object keys and buckets

Confirmed write target from `dags/heartbeat_1m_to_raw.py`:

- bucket: `raw`
- key pattern: `heartbeat/airflow_time_YYYYMMDD_HHMMSS.txt`

Confirmed copy targets:

- `dags/heartbeat_1m_copy_raw_to_conformed.py`
  - source bucket: `raw`
  - destination bucket: `conformed`
  - prefix scanned: `heartbeat/`
  - destination key: same as source key

- `dags/heartbeat_1m_copy_conformed_to_curated.py`
  - source bucket: `conformed`
  - destination bucket: `curated`
  - prefix scanned: `heartbeat/`
  - destination key: same as source key

### Storage destination type

Confirmed from repository inspection:

- writes to MinIO via S3 API
- does not write heartbeat payloads to local disk
- does not write heartbeat payloads to a database
- does not mirror heartbeat artifacts into `data/`

### Partitioning convention

No partition directories are used beyond the prefix `heartbeat/`.

Confirmed key naming convention:

- prefix: `heartbeat/`
- filename stem: `airflow_time_`
- filename timestamp format: `%Y%m%d_%H%M%S`

## Dependencies and runtime assumptions

### Python imports used by the heartbeat DAGs

`dags/heartbeat_1m_to_raw.py`:

- `datetime`
- `os`
- `boto3`
- `pendulum`
- `airflow`
- `airflow.operators.python.PythonOperator`

`dags/heartbeat_1m_copy_raw_to_conformed.py`:

- `datetime`
- `airflow`
- `airflow.operators.python.PythonOperator`
- `boto3`
- `botocore.client.Config`

`dags/heartbeat_1m_copy_conformed_to_curated.py`:

- `datetime`
- `airflow`
- `airflow.operators.python.PythonOperator`
- `boto3`
- `botocore.client.Config`

`notebooks/read_heartbeat.ipynb`:

- `%pip install minio`
- `from minio import Minio`
- `from datetime import timezone`

### Environment variables used

Confirmed direct usage in `dags/heartbeat_1m_to_raw.py`:

- `S3_ENDPOINT_URL`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_DEFAULT_REGION`

Confirmed direct defaults in that file:

- endpoint default: `http://minio:9000`
- access key default: `minioadmin`
- secret key default: `minioadmin`
- region default: `us-east-1`

Confirmed base Airflow environment wiring in `docker-compose.yaml`:

- `S3_ENDPOINT_URL: "http://minio:9000"`
- `AWS_ACCESS_KEY_ID: "${MINIO_ROOT_USER:-minioadmin}"`
- `AWS_SECRET_ACCESS_KEY: "${MINIO_ROOT_PASSWORD:-minioadmin}"`
- `AWS_DEFAULT_REGION: "us-east-1"`

The copy DAGs do not explicitly pass access key or secret key. They instantiate `boto3.client("s3", endpoint_url=MINIO_ENDPOINT, config=Config(signature_version="s3v4"))`, so they rely on the normal boto3 credential resolution chain. In the base stack, those credentials are supplied through the Airflow container environment above.

### Connections and credentials

Confirmed from repository inspection:

- no Airflow connection ID is referenced by heartbeat DAG code
- no external credential file is referenced by heartbeat DAG code
- no heartbeat-specific config JSON or CSV is referenced
- MinIO credentials default to `minioadmin` / `minioadmin` unless overridden through environment

### Bucket names and endpoint URLs

Confirmed:

- endpoint URL: `http://minio:9000`
- buckets: `raw`, `conformed`, `curated`

Bucket creation is handled centrally by `minio-init` in `docker-compose.yaml`:

```sh
mc mb --ignore-existing local/conformed &&
mc mb --ignore-existing local/raw &&
mc mb --ignore-existing local/curated &&
```

### Expected folders and mounts

Confirmed base mounts in `docker-compose.yaml` relevant to heartbeat work:

- `./dags:/opt/airflow/dags`
- `./notebooks:/home/jovyan/work`

The heartbeat DAGs do not require:

- `./config`
- `./scripts`
- `./data`
- `./php`

for their own runtime logic.

### Required Docker Compose services

Confirmed minimum base services involved:

- `minio`
- `minio-init`
- `airflow`

Optional for inspection only:

- `jupyter` for `notebooks/read_heartbeat.ipynb`

Not required for heartbeat DAG execution:

- `php`

## Notebook involvement

Heartbeat-related notebook confirmed:

- `notebooks/read_heartbeat.ipynb`

### What it does

Confirmed from repository inspection:

1. installs or confirms availability of `minio`
2. connects to MinIO at `minio:9000` using `minioadmin` credentials
3. lists objects in bucket `raw` under prefix `heartbeat/`
4. fetches the latest object and prints its contents

### Relationship to the DAGs

The notebook is observational only. It does not implement or trigger the heartbeat DAGs. It reads the artifacts those DAGs create.

### Notebook count

Only one heartbeat-related notebook was found.

## Config involvement

No heartbeat-specific config files were confirmed from repository inspection.

Confirmed negatives:

- no `config/*heartbeat*` files found
- no heartbeat DAG references to JSON, CSV, YAML, or `.env` keys beyond generic S3/AWS environment variables
- no heartbeat-specific config example file exists in overlay examples

## PHP/UI involvement

No heartbeat-specific PHP page or UI file was confirmed from repository inspection.

Confirmed negatives:

- no heartbeat references in `php/index.php`
- no heartbeat references in `php/health.php`
- no heartbeat-specific file under `php/solutions/`

The only PHP mechanism relevant to future overlays is the generic solution discovery/tag system in `php/solutions.php`.

## Overlay contract observations

### Standard overlay folder structure

Confirmed from `overlay_contract/REFERENCE_LAYOUT.md`:

```text
overlay_<name>/
  dev-start-compose.sh
  dev-stop-compose.sh
  dev-docker-compose.overlay-<name>.yaml

  config/
  scripts/
  dags/
  notebooks/
  php/
    solutions/
  data/
    sample/
  docs/

  overlay_<name>/
    start-compose.sh
    stop-compose.sh
    docker-compose.overlay-<name>.yaml
    README.md
    RUNBOOK.md
    .env.example
    docker/
      airflow/
        Dockerfile
      jupyter/
        Dockerfile
```

Minimal file-only pattern also exists:

```text
overlay_<name>/
  php/
    solutions/
      <overlay>_*.php

  overlay_<name>/
    README.md
    RUNBOOK.md
```

### How overlays contribute runtime files

Confirmed whitelist from `overlay_contract/PATH_WHITELIST.md`:

- `./config/<overlay>*.json`
- `./scripts/<overlay>*.py`
- `./dags/dag_<overlay>*.py`
- `./notebooks/<overlay>*.ipynb`
- `./php/solutions/<overlay>*.php`
- `./data/sample/<overlay>/**`
- `./overlay_<name>/**`

This means a future heartbeat overlay should be namespaced. Reusing base file names like `dags/heartbeat_1m_to_raw.py` would not match the documented v1 whitelist.

### How overlays are started and activated

Confirmed from `start-compose.sh`, `stop-compose.sh`, and overlay docs:

- base stack start: `./start-compose.sh`
- compose-enabled overlay start: `./start-compose.sh --overlay <compose-file-or-name>`
- packaged overlay wrappers call the root wrappers with a specific overlay compose file
- file-only overlays do not require `--overlay`

Overlay compose resolution order when a name is supplied:

1. `overlay_<name>/dev-docker-compose.overlay-<slug>.yaml`
2. `overlay_<name>/docker-compose.overlay-<slug>.yaml`
3. `overlay_<name>/overlay_<name>/docker-compose.overlay-<slug>.yaml`

### How overlays are packaged

Confirmed from packaged overlay READMEs:

- overlays are zipped from their outer source-tree folder
- archives install additively into repo root with `unzip -oq <archive>.zip -d .`
- packaged runtime files must live under nested `overlay_<name>/`
- dev helper files remain outside the nested packaged runtime folder and should not be published

### Example overlay runtime patterns

Observed examples:

- `overlay_hello_world`
  - compose-enabled reference overlay
  - includes DAG, scripts, config, notebook, PHP, sample data, Dockerfiles
  - DAG is manual only: `schedule=None`

- `overlay_kaggle_ingestion`
  - compose-enabled ingestion overlay
  - DAG delegates to scripts
  - notebook validates outputs
  - PHP renders curated summary

- `overlay_asx_historic_csv`
  - compose-enabled ingestion overlay
  - DAG delegates to scripts
  - notebook validates outputs
  - PHP reads mirrored curated JSON

- `overlay_file_only_demo`
  - minimal no-compose example
  - contributes only a PHP page

### Implication for `overlay_heartbeat_v2`

A heartbeat overlay probably does not require:

- a custom Airflow image
- a custom Jupyter image
- a PHP solution page
- local mirrored curated JSON
- extra scripts
- config files

It could likely be implemented either as:

1. a file-only additive overlay, if only DAG and optional notebook files are contributed
2. a compose-enabled overlay, if the project wants packaged `start-compose.sh` and `stop-compose.sh` wrappers for consistency with other installable overlays

## Recommended `overlay_heartbeat_v2` file structure

### Likely minimum runtime payload

For faithful recreation of the existing base heartbeat behavior, the likely minimum functional payload is:

- `dags/`

Optional but likely useful:

- `notebooks/`
- `overlay_heartbeat_v2/README.md`
- `overlay_heartbeat_v2/RUNBOOK.md`

Probably unnecessary based on current base heartbeat behavior:

- `scripts/`
- `config/`
- `php/`
- `data/sample/`
- custom Dockerfiles

### Recommended file set

Most conservative overlay adaptation:

- `dags/dag_heartbeat_v2_to_raw.py`
- `dags/dag_heartbeat_v2_copy_raw_to_conformed.py`
- `dags/dag_heartbeat_v2_copy_conformed_to_curated.py`
- `notebooks/heartbeat_v2_validation.ipynb` or similar, if notebook parity is wanted
- `overlay_heartbeat_v2/README.md`
- `overlay_heartbeat_v2/RUNBOOK.md`

Alternative simplification, not confirmed from repository as current behavior:

- one DAG file such as `dags/dag_heartbeat_v2.py` with three tasks

That would be a redesign rather than a direct recreation of the current base implementation.

### Which existing files should be copied or adapted

Most likely adaptation sources:

- `dags/heartbeat_1m_to_raw.py`
- `dags/heartbeat_1m_copy_raw_to_conformed.py`
- `dags/heartbeat_1m_copy_conformed_to_curated.py`
- optionally `notebooks/read_heartbeat.ipynb`

### Required folder assessment

- `dags/`: yes, required
- `scripts/`: probably unnecessary
- `config/`: probably unnecessary
- `notebooks/`: optional
- `php/`: probably unnecessary
- README / runbook docs: recommended
- packaging metadata under `overlay_heartbeat_v2/`: recommended if distributing as an installable overlay archive

## Risks, conflicts, and open questions

### Duplicate scheduled workflows

High risk if the base heartbeat DAGs remain in place.

If the overlay recreates the same workflow with the same schedule while the base DAGs still exist:

- both sets will run every minute
- duplicate heartbeat objects will likely be produced
- bucket contents and health interpretation may become ambiguous

### DAG ID collisions

If overlay DAGs reuse current DAG IDs, Airflow will treat them as the same DAG IDs and behavior will conflict.

Therefore, an overlay-safe implementation should use new DAG IDs such as:

- `heartbeat_v2_to_raw`
- `heartbeat_v2_copy_raw_to_conformed`
- `heartbeat_v2_copy_conformed_to_curated`

or another clearly namespaced variant.

### Output path collisions

If overlay DAGs keep writing to the same buckets and the same `heartbeat/` prefix while the base DAGs also run:

- object-key collisions are possible at minute-level and second-level timing
- copied objects from one workflow can satisfy the other workflow's copy conditions
- it becomes difficult to prove which implementation produced which artifact

Safer coexistence would require a distinct prefix such as:

- `heartbeat_v2/`

or another namespaced output path.

### Schedule choice

Two viable migration-safe choices:

1. keep the one-minute schedule only after the base heartbeat DAGs are removed from the base repo
2. use `schedule=None` or a disabled rollout state during coexistence testing

If the goal is exact behavior parity after migration, the final overlay should probably keep the one-minute schedule. During coexistence, that identical schedule is not safe unless the base DAGs are removed or one side is disabled.

### Contract naming mismatch

The current base heartbeat filenames do not follow the overlay whitelist pattern `dags/dag_<overlay>*.py`.

So a future overlay should adapt filenames to the documented contract rather than copy the base filenames literally.

### Open questions not confirmed from repository inspection

- whether the future overlay should preserve three separate DAGs or consolidate into one DAG
- whether the future overlay must include a packaged compose overlay and wrappers, or can remain file-only
- whether the migration plan will remove the base heartbeat DAGs entirely from `dags/`
- whether the future overlay should preserve the exact `heartbeat/` prefix or intentionally move to a namespaced prefix

## Exact source files inspected

- `README.md`
- `config/README.md`
- `docker-compose.yaml`
- `docker/airflow/Dockerfile`
- `docker/jupyter/Dockerfile`
- `dags/README.md`
- `dags/heartbeat_1m_to_raw.py`
- `dags/heartbeat_1m_copy_raw_to_conformed.py`
- `dags/heartbeat_1m_copy_conformed_to_curated.py`
- `notebooks/read_heartbeat.ipynb`
- `php/index.php`
- `php/health.php`
- `php/solutions.php`
- `docs/reference/IMPLEMENTED_CAPABILITIES.md`
- `overlay_contract/README.md`
- `overlay_contract/CONTRACT.md`
- `overlay_contract/REFERENCE_LAYOUT.md`
- `overlay_contract/RUNBOOK.md`
- `overlay_contract/PATH_WHITELIST.md`
- `overlay_contract/INSTALL_RULES.md`
- `overlay_contract/AIRFLOW_COMPATIBILITY.md`
- `overlay_contract/APPENDIX_HELLO_WORLD.md`
- `overlay_hello_world/dags/dag_hello_world.py`
- `overlay_hello_world/dev-docker-compose.overlay-hello-world.yaml`
- `overlay_hello_world/overlay_hello_world/README.md`
- `overlay_file_only_demo/overlay_file_only_demo/README.md`
- `overlay_kaggle_ingestion/README.md`
- `overlay_kaggle_ingestion/dags/dag_kaggle_ingestion.py`
- `overlay_kaggle_ingestion/overlay_kaggle_ingestion/README.md`
- `overlay_kaggle_ingestion/overlay_kaggle_ingestion/docker-compose.overlay-kaggle.yaml`
- `overlay_asx_historic_csv/dags/dag_asx_historic_csv.py`
- `overlay_asx_historic_csv/docs/explanation.md`
- `overlay_asx_historic_csv/overlay_asx_historic_csv/README.md`
- `overlay_asx_historic_csv/overlay_asx_historic_csv/docker-compose.overlay-asx-historic-csv.yaml`
- `start-compose.sh`
- `stop-compose.sh`

## Exact grep/search commands used

```sh
rg --files
```

```sh
rg -n -i "heartbeat|heartbeat_1m|raw|dag_id|task_id|minio|s3|bucket|notebook|jupyter" .
```

```sh
rg -n -i "heartbeat|heartbeat_1m|airflow_time|copy_new_raw_objects|copy_new_conformed_objects|write_time_to_raw" dags notebooks config php docs README.md docker-compose.yaml start-compose.sh overlay_* overlay_contract
```

```sh
rg -n -i "heartbeat" php config docs notebooks dags README.md overlay_*
```

```sh
rg -n "boto3|botocore|pendulum|airflow|minio" docker dags/heartbeat_1m_to_raw.py dags/heartbeat_1m_copy_raw_to_conformed.py dags/heartbeat_1m_copy_conformed_to_curated.py notebooks/read_heartbeat.ipynb
```

```sh
rg -n -i "conn_id|connection|Variable|getenv|os.getenv|MINIO|S3_ENDPOINT_URL|AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|AWS_DEFAULT_REGION" dags/heartbeat_1m_to_raw.py dags/heartbeat_1m_copy_raw_to_conformed.py dags/heartbeat_1m_copy_conformed_to_curated.py docker-compose.yaml notebooks/read_heartbeat.ipynb
```

## Terminal summary

Current branch at inspection time:

- `main`

Working tree status before report creation:

- clean

File created by this discovery task:

- `docs/internal/discovery_overlay_heartbeat_v2.md`

Unintended file changes:

- none observed during repository inspection
