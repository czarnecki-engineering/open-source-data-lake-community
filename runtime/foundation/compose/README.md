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

`asx_ohlcv` follows the same shape, using real ASX200 market data pulled
live from Yahoo Finance. Trigger these DAGs **in this exact order**, then
run the notebook, exactly as with heartbeat above:

- `asx_ohlcv_raw`
- `asx_ohlcv_raw_to_conformed`
- `asx_ohlcv_conformed_to_curated`
- `asx_ohlcv_curated_to_iceberg`
- notebook: `asx_ohlcv_analysis.ipynb` (`.executed.ipynb` alongside it is
  the same kind of pre-run reference copy as heartbeat's)

`asx_ohlcv_raw` fetches all 201 tickers directly from Yahoo Finance straight
into MinIO's `raw` bucket — no local-disk staging step, each ticker's REST
response goes straight to `s3.put_object` in memory. Live-verified: a full
cold run (no cached data) took under 5 minutes and produced 201/201 raw
CSVs, 201/201 conformed Parquet files, 1 combined curated panel, and 201
Iceberg summary rows (one per ticker) — same proof pattern as heartbeat,
checked independently via `mc ls` and a Trino query, not just Airflow's
green checkmarks.

Same "how to know it worked" pattern applies:
`runtime/shared/data/asx_ohlcv_summary.json` (written by the notebook) will
contain `lake_summary.raw_object_count`, `conformed_object_count`, and
`curated_object_count` all matching the ticker counts above, plus
`trino_row_count: 201`.

There's also a standalone `asx200_ohlcv_local_ingestion` DAG in the same
`runtime/shared/dags/` folder — **it is not part of this pipeline.** It's an
independent utility that downloads the same Yahoo Finance data to local CSV
files under `/opt/airflow/data/raw/`, read by nothing else in this repo.
Easy to mistake for a prerequisite since it sits right next to the real
DAGs; it isn't one.

#### Community edition: `asx_ohlcv` without yFinance

`asx_ohlcv_curated_from_public_source` is a drop-in replacement for
`asx_ohlcv_raw` → `asx_ohlcv_raw_to_conformed` → `asx_ohlcv_conformed_to_curated`
— one DAG instead of three, no Yahoo Finance calls at all. It downloads a
pre-cleaned, already panel-shaped Parquet file from a public GitHub repo
and writes it straight into the same MinIO curated key the three DAGs above
would have produced, so `asx_ohlcv_curated_to_iceberg` reads it completely
unchanged:

1. Trigger `asx_ohlcv_curated_from_public_source`.
2. Trigger `asx_ohlcv_curated_to_iceberg`.
3. Run `asx_ohlcv_analysis.ipynb`, same as the full pipeline.

This is the path the public/community edition of this repo will ship —
only Docker Compose config, no direct external API calls beyond the
one-shot GitHub fetch. `asx_ohlcv_raw` and friends stay in this repo but
won't be carried over to that edition.

**One thing to know if you ever run both paths in the same environment on
the same day**: `asx_ohlcv_curated_to_iceberg` dedupes by `(ticker,
run_date)` only — it doesn't know which ingestion path produced the
curated panel it's summarising. Whichever path's `curated_to_iceberg` run
completes *first* on a given day "wins" for that day; the second run's
(possibly different) numbers are silently skipped, not merged. This never
actually happens in a real deployment — the full edition only runs the
yFinance path, the community edition only runs the public-source path —
it only matters if you deliberately run both in the same sandbox, as this
repo's own testing does. See the comment at `_existing_run_keys` in
`runtime/shared/dags/asx_ohlcv_runtime.py` for the live-reproduced detail.

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
