# Foundation Compose Slice

The Docker Compose baseline slice of the Knowledge Lake runtime: `minio`,
`frankenphp`, `postgres`, `lakekeeper`, `trino`, `airflow-web` +
`airflow-scheduler`, `jupyter`, `cloudbeaver`, plus the one-shot `minio-init`
and `airflow-init` bootstrap jobs.

## Quickstart

Prerequisite: Docker Desktop (or another local Docker daemon) must already be
running — `start-compose.sh` builds and starts containers, so it needs the
daemon reachable first. If it isn't running, `start-compose.sh` fails fast
with `Error: Docker daemon is not running.`

From the repository root, create and activate the local Python environment,
then install the packages used by the tests:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pandas yfinance scipy pyarrow boto3
python -m unittest discover -s tests -p 'test_*.py'
```

Then start and validate the Compose runtime:

```bash
cp runtime/shared/.env.example runtime/shared/.env   # first time only — skip if runtime/shared/.env already exists
bash runtime/foundation/compose/start-compose.sh
bash runtime/foundation/compose/smoke-test.sh
bash runtime/foundation/compose/validate-config-first.sh
```

`smoke-test.sh` and `validate-config-first.sh` mirror
[`runtime/knowledge-lake/smoke-test.sh`](../../knowledge-lake/smoke-test.sh)
and [`validate-config-first.sh`](../../knowledge-lake/validate-config-first.sh)
— same checks, same PASS/FAIL conventions, adapted for `docker exec` instead
of `kubectl exec`.

When you're done:
```bash
bash runtime/foundation/compose/stop-compose.sh
bash runtime/foundation/compose/stop-compose.sh --volumes   # also wipes named volumes (full reset)
```

## Local URLs And Logins

Ports are configurable in `runtime/shared/.env`; defaults shown. Credential
values are whatever `runtime/shared/.env` currently has set for that
variable.

| Service | URL | Login |
| --- | --- | --- |
| FrankenPHP homepage | http://127.0.0.1:8088/index.php | none — public entry point |
| FrankenPHP health | http://127.0.0.1:8088/health.php | none |
| MinIO API | http://127.0.0.1:9000 | `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` |
| MinIO Console | http://127.0.0.1:9001 | `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` |
| Airflow Web | http://127.0.0.1:8080 | `AIRFLOW_USERNAME` / `AIRFLOW_PASSWORD` |
| Jupyter | http://127.0.0.1:8888 | none — tokenless (`JUPYTER_TOKEN` empty) |
| CloudBeaver | http://127.0.0.1:8978 | self-provisioned — create the admin account yourself on first visit |
| Lakekeeper | http://127.0.0.1:8181 | none — `AUTHZ_BACKEND: allowall` |
| Trino | http://127.0.0.1:8085 | none — no auth configured |
| Postgres | localhost:5432 | `POSTGRES_USER` / `POSTGRES_PASSWORD` |

## Running A Solution

A "solution" is a named, self-contained pipeline — DAGs plus a PHP page,
optionally a notebook — following the shape defined in the
[Solution Contract](../../../docs/runtime/shared/SOLUTION_CONTRACT.md). Two
ship in this repo: `heartbeat` (the minimal proving slice) and `asx_ohlcv`
(a full real-data pipeline).

To manually run the heartbeat slice end to end, once the stack above is up:

1. Open **Airflow Web** and log in (see table above).
2. Trigger these DAGs **in this exact order**, waiting for each to finish
   (green) before triggering the next — each reads the previous stage's
   output, so out-of-order runs fail:
   - `heartbeat_raw`
   - `heartbeat_raw_to_conformed`
   - `heartbeat_conformed_to_curated`
   - `heartbeat_curated_to_iceberg`
3. Open **Jupyter** (see table above) and run
   `runtime/shared/notebooks/heartbeat_analysis.ipynb` top to bottom — it
   reads the Iceberg table the DAGs above just populated, then saves its own
   summary back through the mount.
   (`heartbeat_analysis.executed.ipynb` alongside it is a pre-run reference
   copy with outputs already baked in — for comparison only, not meant to be
   edited or re-run.)

**How to know it actually worked** — no `docker exec` or CLI needed, just
look at these two files on your own machine after step 3:
- `runtime/shared/notebooks/heartbeat_analysis.ipynb` — reopen it; the code
  cells should show populated output (not blank), and the last cell's output
  should include an `event_id` and `event_timestamp` matching whatever
  moment you ran `heartbeat_raw` at.
- `runtime/shared/data/heartbeat_summary.json` — this file is written by the
  notebook itself. Its existence and its `event_id` matching the notebook's
  output is your end-to-end proof: Airflow moved data through MinIO and into
  the Iceberg table, and Jupyter read it back out and saved state into the
  shared folder, all in one unbroken chain.

`asx_ohlcv` follows the same shape, using real ASX market data pulled live
from Yahoo Finance. For the publication/research workflow, trigger these
DAGs **in this exact order**, waiting for each to finish green before
triggering the next:

1. `asx_ohlcv_raw`
2. `asx_ohlcv_raw_to_conformed`
3. `asx_ohlcv_conformed_to_curated`
4. `asx_ohlcv_curated_to_iceberg`
5. `asx_sector_map_curated`

Then open **Jupyter** and run
`runtime/shared/notebooks/asx_publication_research.ipynb` top to bottom.
The sector-map DAG supplies the current Yahoo-derived ASX sector reference
used by the pairs-trading research in that notebook.

`asx_ohlcv_raw` fetches the configured ticker universe directly from Yahoo
Finance straight into MinIO's `raw` bucket — no local-disk staging step;
each ticker's response goes straight to `s3.put_object` in memory. The
subsequent DAGs convert those objects to conformed Parquet, build the curated
panel, publish the Iceberg summary, and build the sector reference used by
the publication notebook.

The earlier `asx_ohlcv_analysis.ipynb` remains available for the basic ASX
pipeline analysis, but `asx_publication_research.ipynb` is the notebook for
the publication/research workflow above.

## Troubleshooting

Something not matching the above? Read
[`docs/runtime/compose/TROUBLESHOOTING.md`](../../../docs/runtime/compose/TROUBLESHOOTING.md)
before digging further — it covers known failure modes and their fixes.

## Reference

Internals for anyone changing this slice, not needed to just run it.

Design rules:
- service names align with the Team repo Kubernetes names
- authored repo mounts come from `runtime/shared/*`
- persistent internal state stays restricted to named volumes
- no root-level `./php`, `./config`, `./data`, or `./scripts` bind mounts are used here

Current authored mounts:
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
- CloudBeaver keeps only internal workspace state in the named volume `cloudbeaver-workspace`
- Trino keeps only internal coordinator state in the named volume `trino-data`
