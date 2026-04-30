# Heartbeat v2 Overlay Runbook

## Purpose

`overlay_heartbeat_v2` recreates the base heartbeat workflow as an additive overlay.

It writes timestamp text files into MinIO bucket `raw` under `heartbeat_v2/`, then copies new objects into bucket `conformed` and bucket `curated` with the same object keys.

## Runtime behavior

- Airflow DAG `heartbeat_v2_to_raw` writes timestamp payloads every minute
- Airflow DAG `heartbeat_v2_copy_raw_to_conformed` copies new `raw/heartbeat_v2/*` objects into `conformed/heartbeat_v2/*`
- Airflow DAG `heartbeat_v2_copy_conformed_to_curated` copies new `conformed/heartbeat_v2/*` objects into `curated/heartbeat_v2/*`
- all DAGs use `catchup=False`

## Source-tree development mode

From the repository root:

```bash
bash overlay_heartbeat_v2/dev-start-compose.sh
```

This mounts:

- `overlay_heartbeat_v2/dags` into the Airflow DAG scan path
- `overlay_heartbeat_v2/notebooks` into Jupyter work area

Stop:

```bash
bash overlay_heartbeat_v2/dev-stop-compose.sh
```

To remove volumes during cleanup:

```bash
bash overlay_heartbeat_v2/dev-stop-compose.sh --volumes
```

## Archive build

From the repository root:

```bash
cd overlay_heartbeat_v2
zip -rq ../overlay_heartbeat_v2.zip dags notebooks overlay_heartbeat_v2
```

The archive installs additively and should contain:

- `dags/dag_heartbeat_v2_to_raw.py`
- `dags/dag_heartbeat_v2_copy_raw_to_conformed.py`
- `dags/dag_heartbeat_v2_copy_conformed_to_curated.py`
- `notebooks/heartbeat_v2_validation.ipynb`
- `overlay_heartbeat_v2/README.md`
- `overlay_heartbeat_v2/RUNBOOK.md`
- `overlay_heartbeat_v2/start-compose.sh`
- `overlay_heartbeat_v2/stop-compose.sh`

## Install from zip

From the repository root of a compatible Community checkout:

```bash
unzip -oq overlay_heartbeat_v2.zip -d .
```

Start:

```bash
bash overlay_heartbeat_v2/start-compose.sh
```

Equivalent base start path:

```bash
bash start-compose.sh
```

Stop:

```bash
bash overlay_heartbeat_v2/stop-compose.sh
```

Reset volumes if needed:

```bash
bash overlay_heartbeat_v2/stop-compose.sh --volumes
```

## Validation steps

### Airflow

Confirm DAG IDs:

- `heartbeat_v2_to_raw`
- `heartbeat_v2_copy_raw_to_conformed`
- `heartbeat_v2_copy_conformed_to_curated`

### MinIO

Confirm objects appear under:

- `raw/heartbeat_v2/`
- `conformed/heartbeat_v2/`
- `curated/heartbeat_v2/`

### Notebook

Open:

- `notebooks/heartbeat_v2_validation.ipynb`

It reads the latest object from `raw/heartbeat_v2/` and displays the payload.

## Coexistence with base heartbeat

The overlay does not remove, rename, disable, or alter the base heartbeat DAGs.

Coexistence is safe because:

- DAG IDs differ from the base heartbeat DAGs
- the object prefix is `heartbeat_v2/` instead of `heartbeat/`
