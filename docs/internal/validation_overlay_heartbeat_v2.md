# Validation: `overlay_heartbeat_v2`

## Branch and baseline

- branch: `main`
- commit hash before changes: `a5005cff29219b73c181af4bf554b973200715fc`

## Files created

Overlay source tree:

- `overlay_heartbeat_v2/dags/dag_heartbeat_v2_to_raw.py`
- `overlay_heartbeat_v2/dags/dag_heartbeat_v2_copy_raw_to_conformed.py`
- `overlay_heartbeat_v2/dags/dag_heartbeat_v2_copy_conformed_to_curated.py`
- `overlay_heartbeat_v2/dev-docker-compose.overlay-heartbeat-v2.yaml`
- `overlay_heartbeat_v2/dev-start-compose.sh`
- `overlay_heartbeat_v2/dev-stop-compose.sh`
- `overlay_heartbeat_v2/notebooks/heartbeat_v2_validation.ipynb`
- `overlay_heartbeat_v2/overlay_heartbeat_v2/README.md`
- `overlay_heartbeat_v2/overlay_heartbeat_v2/RUNBOOK.md`
- `overlay_heartbeat_v2/overlay_heartbeat_v2/start-compose.sh`
- `overlay_heartbeat_v2/overlay_heartbeat_v2/stop-compose.sh`

Repository docs and artifacts:

- `docs/internal/discovery_overlay_heartbeat_v2.md`
- `docs/internal/validation_overlay_heartbeat_v2.md`
- `overlay_heartbeat_v2.zip`

## Zip archive

- archive name: `overlay_heartbeat_v2.zip`
- archive location: repository root
- install command:

```bash
unzip -oq overlay_heartbeat_v2.zip -d .
```

### Archive contents summary

Confirmed with `unzip -l overlay_heartbeat_v2.zip`.

Archive payload:

- `dags/dag_heartbeat_v2_to_raw.py`
- `dags/dag_heartbeat_v2_copy_raw_to_conformed.py`
- `dags/dag_heartbeat_v2_copy_conformed_to_curated.py`
- `notebooks/heartbeat_v2_validation.ipynb`
- `overlay_heartbeat_v2/README.md`
- `overlay_heartbeat_v2/RUNBOOK.md`
- `overlay_heartbeat_v2/start-compose.sh`
- `overlay_heartbeat_v2/stop-compose.sh`

This matched the intended additive install layout.

## Commands used

### Archive build and inspection

```bash
cd overlay_heartbeat_v2
zip -rq ../overlay_heartbeat_v2.zip dags notebooks overlay_heartbeat_v2
```

```bash
unzip -l overlay_heartbeat_v2.zip
```

### Shared validation commands

Airflow DAG inspection:

```bash
docker exec airflow airflow dags list | rg "heartbeat"
```

Airflow DAG run inspection:

```bash
docker exec airflow airflow dags list-runs -d heartbeat_1m_to_raw -o plain
docker exec airflow airflow dags list-runs -d heartbeat_v2_to_raw -o plain
docker exec airflow airflow dags list-runs -d heartbeat_1m_copy_conformed_to_curated -o plain
docker exec airflow airflow dags list-runs -d heartbeat_v2_copy_conformed_to_curated -o plain
```

MinIO / S3 object inspection:

```bash
docker exec airflow python -c "import boto3, json; s3=boto3.client('s3', endpoint_url='http://minio:9000', aws_access_key_id='minioadmin', aws_secret_access_key='minioadmin'); prefixes=['heartbeat/','heartbeat_v2/']; data={}; \
for prefix in prefixes: \
    data[prefix]={bucket: sorted(obj['Key'] for obj in s3.list_objects_v2(Bucket=bucket, Prefix=prefix).get('Contents', [])) for bucket in ['raw','conformed','curated']}; \
print(json.dumps(data, indent=2))"
```

Airflow health:

```bash
curl -fsS http://localhost:8080/health
```

Wait for scheduler cycles:

```bash
sleep 70
```

## Test configuration 1: base Docker stack only

### Start / stop commands

```bash
./stop-compose.sh --volumes
bash start-compose.sh
```

### Validation commands used

```bash
curl -fsS http://localhost:8080/health
docker exec airflow airflow dags list | rg "heartbeat|dag_id"
docker exec airflow python -c "..."
```

### Results

Confirmed:

- base heartbeat DAGs present:
  - `heartbeat_1m_to_raw`
  - `heartbeat_1m_copy_raw_to_conformed`
  - `heartbeat_1m_copy_conformed_to_curated`
- no `heartbeat_v2_*` DAGs present
- MinIO objects present under:
  - `raw/heartbeat/`
  - `conformed/heartbeat/`
  - `curated/heartbeat/`
- no `heartbeat_v2/` objects produced

Observed object snapshot:

```text
heartbeat/raw:        heartbeat/airflow_time_20260428_160126.txt
heartbeat/conformed:  heartbeat/airflow_time_20260428_160126.txt
heartbeat/curated:    heartbeat/airflow_time_20260428_160126.txt
heartbeat_v2/*:       none
```

Status: passed

## Test configuration 2: base + `overlay_heartbeat_v2` in source-tree/dev mode

### Start / stop commands

Reset:

```bash
./stop-compose.sh --volumes
```

Start with the supported root overlay mechanism:

```bash
bash start-compose.sh --overlay overlay_heartbeat_v2/dev-docker-compose.overlay-heartbeat-v2.yaml
```

Stop with the same overlay argument:

```bash
bash stop-compose.sh --overlay overlay_heartbeat_v2/dev-docker-compose.overlay-heartbeat-v2.yaml --volumes
```

### Validation commands used

```bash
curl -fsS http://localhost:8080/health
docker exec airflow airflow dags list | rg "heartbeat"
docker exec airflow airflow dags list-runs -d heartbeat_1m_to_raw -o plain
docker exec airflow airflow dags list-runs -d heartbeat_v2_to_raw -o plain
docker exec airflow airflow dags list-runs -d heartbeat_1m_copy_conformed_to_curated -o plain
docker exec airflow airflow dags list-runs -d heartbeat_v2_copy_conformed_to_curated -o plain
docker exec airflow python -c "..."
```

### Results

Confirmed:

- base heartbeat DAGs still present
- overlay heartbeat DAGs present:
  - `heartbeat_v2_to_raw`
  - `heartbeat_v2_copy_raw_to_conformed`
  - `heartbeat_v2_copy_conformed_to_curated`
- no DAG ID collisions
- overlay DAG file locations were under `/opt/airflow/dags/overlay_heartbeat_v2/...`
- base objects continued under `heartbeat/`
- overlay objects were written under `heartbeat_v2/`
- no object prefix collisions observed

Observed object snapshot near the end of validation:

```text
heartbeat/raw:        heartbeat/airflow_time_20260428_160416.txt
heartbeat/raw:        heartbeat/airflow_time_20260428_160514.txt
heartbeat/raw:        heartbeat/airflow_time_20260428_160645.txt
heartbeat/conformed:  heartbeat/airflow_time_20260428_160416.txt
heartbeat/conformed:  heartbeat/airflow_time_20260428_160514.txt
heartbeat/curated:    heartbeat/airflow_time_20260428_160416.txt
heartbeat/curated:    heartbeat/airflow_time_20260428_160514.txt

heartbeat_v2/raw:        heartbeat_v2/airflow_time_20260428_160345.txt
heartbeat_v2/raw:        heartbeat_v2/airflow_time_20260428_160439.txt
heartbeat_v2/raw:        heartbeat_v2/airflow_time_20260428_160541.txt
heartbeat_v2/raw:        heartbeat_v2/airflow_time_20260428_160608.txt
heartbeat_v2/conformed:  heartbeat_v2/airflow_time_20260428_160345.txt
heartbeat_v2/conformed:  heartbeat_v2/airflow_time_20260428_160439.txt
heartbeat_v2/conformed:  heartbeat_v2/airflow_time_20260428_160541.txt
heartbeat_v2/conformed:  heartbeat_v2/airflow_time_20260428_160608.txt
heartbeat_v2/curated:    heartbeat_v2/airflow_time_20260428_160345.txt
heartbeat_v2/curated:    heartbeat_v2/airflow_time_20260428_160439.txt
heartbeat_v2/curated:    heartbeat_v2/airflow_time_20260428_160541.txt
heartbeat_v2/curated:    heartbeat_v2/airflow_time_20260428_160608.txt
```

Note:

- because the stack uses `SequentialExecutor`, individual buckets were sometimes one run behind during intermediate checks
- final assertions were taken only after additional scheduler waits confirmed steady-state behavior

Status: passed

## Test configuration 3: base + `overlay_heartbeat_v2` installed from zip archive

### Temporary clean checkout setup

Created a clean temp checkout at the pre-change commit:

```bash
mktemp -d /tmp/overlay-heartbeat-v2-archive-test.XXXXXX
git worktree add /tmp/overlay-heartbeat-v2-archive-test.yciikf a5005cff29219b73c181af4bf554b973200715fc
cp /Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/overlay_heartbeat_v2.zip /tmp/overlay-heartbeat-v2-archive-test.yciikf/
```

Installed the archive:

```bash
cd /tmp/overlay-heartbeat-v2-archive-test.yciikf
unzip -oq overlay_heartbeat_v2.zip -d .
```

Confirmed installed archive layout:

```bash
ls -1 dags | rg "heartbeat"
ls -1 overlay_heartbeat_v2
ls -1 notebooks | rg "heartbeat_v2|read_heartbeat"
```

### Start / stop commands

Installed wrapper attempt:

```bash
bash overlay_heartbeat_v2/start-compose.sh
```

Equivalent installed root-runtime start path:

```bash
bash start-compose.sh
```

Stop:

```bash
bash stop-compose.sh --volumes
```

Cleanup:

```bash
git worktree remove --force /tmp/overlay-heartbeat-v2-archive-test.yciikf
```

### Validation commands used

```bash
curl -fsS http://localhost:8080/health
docker exec airflow airflow dags list | rg "heartbeat"
docker exec airflow airflow dags list-runs -d heartbeat_v2_to_raw -o plain
docker exec airflow airflow dags list-runs -d heartbeat_v2_copy_conformed_to_curated -o plain
docker exec airflow python -c "..."
```

### Results

Confirmed installed layout:

- `dags/dag_heartbeat_v2_to_raw.py`
- `dags/dag_heartbeat_v2_copy_raw_to_conformed.py`
- `dags/dag_heartbeat_v2_copy_conformed_to_curated.py`
- `notebooks/heartbeat_v2_validation.ipynb`
- `overlay_heartbeat_v2/README.md`
- `overlay_heartbeat_v2/RUNBOOK.md`
- `overlay_heartbeat_v2/start-compose.sh`
- `overlay_heartbeat_v2/stop-compose.sh`

Confirmed runtime behavior from the installed archive:

- overlay heartbeat DAGs present from installed root `dags/`
- base heartbeat DAGs still present
- base objects present under `heartbeat/`
- overlay objects present under `heartbeat_v2/`
- installed archive layout matched the overlay contract's additive root-runtime pattern

Observed object snapshot near the end of validation:

```text
heartbeat/raw:        heartbeat/airflow_time_20260428_161009.txt
heartbeat/raw:        heartbeat/airflow_time_20260428_161133.txt
heartbeat/conformed:  heartbeat/airflow_time_20260428_161009.txt
heartbeat/conformed:  heartbeat/airflow_time_20260428_161133.txt
heartbeat/curated:    heartbeat/airflow_time_20260428_161009.txt
heartbeat/curated:    heartbeat/airflow_time_20260428_161133.txt

heartbeat_v2/raw:        heartbeat_v2/airflow_time_20260428_161049.txt
heartbeat_v2/raw:        heartbeat_v2/airflow_time_20260428_161139.txt
heartbeat_v2/raw:        heartbeat_v2/airflow_time_20260428_161207.txt
heartbeat_v2/conformed:  heartbeat_v2/airflow_time_20260428_161049.txt
heartbeat_v2/curated:    heartbeat_v2/airflow_time_20260428_161049.txt
```

Status: passed

## Failures and fixes

### 1. Initial archive build path mistake

Issue:

- the first `zip` command wrote `overlay_heartbeat_v2.zip` inside `overlay_heartbeat_v2/` instead of the repository root

Fix:

- removed the misplaced archive
- rebuilt using:

```bash
cd overlay_heartbeat_v2
zip -rq ../overlay_heartbeat_v2.zip dags notebooks overlay_heartbeat_v2
```

### 2. Early Airflow CLI checks during startup

Issue:

- some early `docker exec airflow airflow dags list` checks returned:

```text
ERROR: You need to initialize the database. Please run `airflow db init`.
```

Cause:

- Airflow container startup had not completed yet

Fix:

- waited for `curl -fsS http://localhost:8080/health`
- added `sleep 70` waits between validation passes

### 3. Installed wrapper invocation under Codex sandbox

Issue:

- the direct installed wrapper invocation:

```bash
bash overlay_heartbeat_v2/start-compose.sh
```

returned:

```text
Error: Docker daemon is not running. Start Docker Desktop and try again.
```

Cause:

- not confirmed as a repository problem
- observed only when invoking the installed wrapper through the Codex tool sandbox

Fix / workaround used for validation:

- started the installed archive layout through the equivalent root runtime path:

```bash
bash start-compose.sh
```

- this is valid because the installed `overlay_heartbeat_v2/start-compose.sh` wrapper is only a convenience delegate to the root `start-compose.sh`
- packaged docs were updated to state this equivalent path explicitly

## Final git status

Main repository status at the end of validation, before staging and commit, was expected to include:

- the new `overlay_heartbeat_v2/` source tree
- `overlay_heartbeat_v2.zip`
- `docs/internal/validation_overlay_heartbeat_v2.md`
- `docs/internal/discovery_overlay_heartbeat_v2.md`

No unrelated repository files were intentionally modified during this work.
