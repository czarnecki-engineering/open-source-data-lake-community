# overlay_heartbeat_v2

This overlay recreates the existing base heartbeat workflow as an additive runtime overlay.

It preserves the current heartbeat behavior as closely as possible:

- three separate Airflow DAGs
- one-minute schedules
- `catchup=False`
- plain-text timestamp payloads
- MinIO / S3 writes through `boto3`
- raw -> conformed -> curated copy pattern

The only functional difference from the base heartbeat is the object prefix:

- base heartbeat prefix: `heartbeat/`
- overlay heartbeat prefix: `heartbeat_v2/`

This allows the base heartbeat and overlay heartbeat to coexist safely.

## Runtime contents

- `dags/dag_heartbeat_v2_to_raw.py`
- `dags/dag_heartbeat_v2_copy_raw_to_conformed.py`
- `dags/dag_heartbeat_v2_copy_conformed_to_curated.py`
- `notebooks/heartbeat_v2_validation.ipynb`
- `overlay_heartbeat_v2/README.md`
- `overlay_heartbeat_v2/RUNBOOK.md`

## Buckets and object prefix

The overlay writes to the same MinIO buckets as the base workflow:

- `raw`
- `conformed`
- `curated`

It uses only the `heartbeat_v2/` prefix:

- `raw/heartbeat_v2/...`
- `conformed/heartbeat_v2/...`
- `curated/heartbeat_v2/...`

## Dev / source-tree mode

From the repository root:

```bash
bash overlay_heartbeat_v2/dev-start-compose.sh
```

Stop:

```bash
bash overlay_heartbeat_v2/dev-stop-compose.sh
```

This activates the overlay through:

```bash
./start-compose.sh --overlay overlay_heartbeat_v2/dev-docker-compose.overlay-heartbeat-v2.yaml
```

## Zip install

Install into a compatible Community checkout from the repository root:

```bash
unzip -oq overlay_heartbeat_v2.zip -d .
```

After install, the overlay DAGs and notebook are available through the base runtime mounts. Start the stack with:

```bash
bash overlay_heartbeat_v2/start-compose.sh
```

Equivalent base start path:

```bash
bash start-compose.sh
```

Stop with:

```bash
bash overlay_heartbeat_v2/stop-compose.sh
```

## Validation

In Airflow, confirm these DAG IDs are present:

- `heartbeat_v2_to_raw`
- `heartbeat_v2_copy_raw_to_conformed`
- `heartbeat_v2_copy_conformed_to_curated`

In MinIO, confirm objects appear under:

- `raw/heartbeat_v2/`
- `conformed/heartbeat_v2/`
- `curated/heartbeat_v2/`

Optional notebook:

- `notebooks/heartbeat_v2_validation.ipynb`

## Difference from the base heartbeat

The base repository ships these DAG IDs:

- `heartbeat_1m_to_raw`
- `heartbeat_1m_copy_raw_to_conformed`
- `heartbeat_1m_copy_conformed_to_curated`

This overlay adds:

- `heartbeat_v2_to_raw`
- `heartbeat_v2_copy_raw_to_conformed`
- `heartbeat_v2_copy_conformed_to_curated`

The base and overlay flows can run together because their DAG IDs and object prefixes do not collide.

The packaged wrapper scripts are convenience delegates only:

- `overlay_heartbeat_v2/start-compose.sh` delegates to the root `start-compose.sh`
- `overlay_heartbeat_v2/stop-compose.sh` delegates to the root `stop-compose.sh`
