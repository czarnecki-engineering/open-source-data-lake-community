# Community Docker Compose Runtime

The Docker Compose runtime for Open Source Data Lake Community. It runs `minio`, `frankenphp`, `postgres`, `lakekeeper`, `trino`, `airflow-web`, `airflow-scheduler`, `jupyter`, and `cloudbeaver`, plus the one-shot bootstrap jobs used to initialise the runtime.

## Quickstart

Prerequisite: Docker Desktop, or another local Docker daemon with Docker Compose v2, must already be running. `start-compose.sh` builds and starts the containers and fails fast if Docker is unavailable.

From the repository root, create and activate a local Python environment if you want to run the repository tests:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pandas yfinance scipy pyarrow boto3
python -m unittest discover -s tests -p 'test_*.py'
```

Create the local runtime configuration on first use:

```bash
cp runtime/shared/.env.example runtime/shared/.env
```

Then start and validate the Community runtime:

```bash
bash runtime/foundation/compose/start-compose.sh
bash runtime/foundation/compose/smoke-test.sh
bash runtime/foundation/compose/validate-config-first.sh
```

When you're done:

```bash
bash runtime/foundation/compose/stop-compose.sh
```

For a full reset that also removes named volumes:

```bash
bash runtime/foundation/compose/stop-compose.sh --volumes
```

## Local URLs And Logins

Ports are configurable in `runtime/shared/.env`; defaults are shown below. Credential values are whatever `runtime/shared/.env` currently has set for the corresponding variable.

| Service | URL | Login |
| --- | --- | --- |
| FrankenPHP homepage | http://127.0.0.1:8088/index.php | none — public entry point |
| FrankenPHP health | http://127.0.0.1:8088/health.php | none |
| MinIO API | http://127.0.0.1:9000 | `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` |
| MinIO Console | http://127.0.0.1:9001 | `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` |
| Airflow Web | http://127.0.0.1:8080 | `AIRFLOW_USERNAME` / `AIRFLOW_PASSWORD` |
| Jupyter | http://127.0.0.1:8888 | none — tokenless (`JUPYTER_TOKEN` empty) |
| CloudBeaver | http://127.0.0.1:8978 | self-provisioned — create the admin account on first visit |
| Lakekeeper | http://127.0.0.1:8181 | none — `AUTHZ_BACKEND: allowall` |
| Trino | http://127.0.0.1:8085 | none — no auth configured |
| Postgres | localhost:5432 | `POSTGRES_USER` / `POSTGRES_PASSWORD` |

## Included Workloads

The repository ships with two demonstration workloads: `heartbeat` and `asx_ohlcv`. Their authored files live under `runtime/shared/` and are mounted directly into the relevant runtime containers.

### Heartbeat

To run the heartbeat workload end to end once the stack is up:

1. Open **Airflow Web** and log in using the credentials above.
2. Trigger these DAGs in this exact order, waiting for each to finish successfully before triggering the next:
   - `heartbeat_raw`
   - `heartbeat_raw_to_conformed`
   - `heartbeat_conformed_to_curated`
   - `heartbeat_curated_to_iceberg`
3. Open **Jupyter** and run `heartbeat_analysis.ipynb` from top to bottom.

The notebook reads the Iceberg table populated by the DAG chain and writes `runtime/shared/data/heartbeat_summary.json` through the shared mount.

A successful end-to-end run is demonstrated by populated notebook output and a generated `runtime/shared/data/heartbeat_summary.json` whose event data corresponds to the heartbeat run.

### ASX OHLCV

The ASX workload uses real market data retrieved from Yahoo Finance.

For the publication/research workflow, trigger these DAGs in this exact order, waiting for each to finish successfully before triggering the next:

1. `asx_ohlcv_raw`
2. `asx_ohlcv_raw_to_conformed`
3. `asx_ohlcv_conformed_to_curated`
4. `asx_ohlcv_curated_to_iceberg`
5. `asx_sector_map_curated`

Then open **Jupyter** and run `asx_publication_research.ipynb` from top to bottom.

`asx_ohlcv_raw` fetches the configured ticker universe directly from Yahoo Finance into MinIO without a local-disk staging step. Subsequent DAGs convert the source objects to conformed Parquet, build the curated panel, publish the Iceberg summary, and build the sector reference used by the research notebook.

## Runtime Mounts

Authored repository content is mounted directly from `runtime/shared/`. Persistent service state is kept in Docker named volumes where configured.

Current authored mounts include:

- `runtime/shared/php -> /app/public`
- `runtime/shared/config -> /app/config`
- `runtime/shared/data -> /app/data`
- `runtime/shared/dags -> /opt/airflow/dags`
- `runtime/shared/config -> /opt/airflow/config`
- `runtime/shared/data -> /opt/airflow/data`
- `runtime/shared/scripts -> /opt/airflow/scripts`
- `runtime/shared/trino/* -> /etc/trino/*`
- `runtime/shared/notebooks -> /home/jovyan/work`
- `runtime/shared/config -> /home/jovyan/config`
- `runtime/shared/data -> /home/jovyan/data`
- `runtime/shared/scripts -> /home/jovyan/scripts`

CloudBeaver and other services that require internal runtime state use the named volumes defined in `docker-compose.yaml`.

## Configuration

`runtime/shared/.env` is the local runtime configuration file. Start from the tracked template:

```bash
cp runtime/shared/.env.example runtime/shared/.env
```

The startup script passes this file to Docker Compose. If it is absent, the runtime uses defaults defined by the Compose configuration where available and prints a warning.

## Troubleshooting

For known Community runtime failure modes and recovery commands, see [`docs/runtime/compose/TROUBLESHOOTING.md`](../../../docs/runtime/compose/TROUBLESHOOTING.md).

The Compose file, Dockerfiles and operational scripts in this directory are authoritative for the implemented runtime.
