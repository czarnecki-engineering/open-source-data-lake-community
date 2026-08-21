# Compose Runtime Troubleshooting

Operational FAQ for the Docker Compose local runtime. See
[`docs/runtime/knowledge-lake/TROUBLESHOOTING.md`](../knowledge-lake/TROUBLESHOOTING.md)
for the Kubernetes equivalent — the two stacks share `runtime/shared/` but
have different failure modes, documented separately rather than merged.

## 1. Before You Debug Anything

- All commands run from the **repository root**.
- **Docker Desktop** is running (`docker info` succeeds).
- **`runtime/shared/.env` exists** — `cp runtime/shared/.env.example runtime/shared/.env`. Both Compose and Kubernetes read credentials/config from this one file; without it, Compose falls back to the defaults baked into `docker-compose.yaml` (harmless for local dev, but you won't be able to customize anything).
- **Nothing else is bound to the same ports.** Compose and the Kubernetes stack default to the *same* localhost ports (8088, 8888, 8080, 8085, 8181, 9000/9001, 8978). They cannot run at the same time. If you were just running the Kubernetes stack, stop its port-forwards first: `runtime/knowledge-lake/stop-k8s.sh` (this only stops the port-forwards, not the cluster, so switching back later is cheap).

## 2. Golden Startup Path

```bash
bash runtime/foundation/compose/start-compose.sh
bash runtime/foundation/compose/smoke-test.sh
bash runtime/foundation/compose/validate-config-first.sh
```

Then open `http://127.0.0.1:8088/index.php`.

## 3. Mandatory First Checks

```bash
docker compose -f runtime/foundation/compose/docker-compose.yaml ps
```

Every service should show `Up` (init/migrate jobs like `airflow-init`,
`minio-init`, `lakekeeper-migrate` show `Exited (0)` once complete — that's
success, not a failure).

## 4. Known Failure Modes and Fixes

### 4.1 Port already in use

**Symptom:** `start-compose.sh` fails immediately, or `docker compose up`
reports a port is already allocated.

**Cause:** Almost always the Kubernetes stack's port-forwards are still
running — see §1. Less commonly, some other local process is using the port.

**Fix:**
```bash
bash runtime/knowledge-lake/stop-k8s.sh
lsof -nP -iTCP:8088 -sTCP:LISTEN   # find anything else still holding a port
```

### 4.2 `airflow-web` / `airflow-scheduler` show `health: starting` for a while

**Expected behavior**, not a failure — first boot takes longer than the
default poll interval suggests. Give it 30–60 seconds and recheck:

```bash
docker inspect --format '{{.State.Health.Status}}' airflow-web
```

If it's still not `healthy` after a few minutes, check logs:
```bash
docker logs airflow-web --tail=50
```

### 4.3 `Found orphan containers` warning on startup

**Symptom:** `start-compose.sh` prints a warning about orphan containers
(e.g. a service that no longer exists in `docker-compose.yaml` but has a
leftover container from an older version of the file).

**Expected behavior for a stack that's been edited over time.** Not a
failure. Clean it up with:
```bash
docker compose -f runtime/foundation/compose/docker-compose.yaml up -d --remove-orphans
```

### 4.4 Changes to a Dockerfile or `AIRFLOW_PIP_ADDITIONAL_REQUIREMENTS` don't take effect

**Cause:** `start-compose.sh` builds images every run, but Docker's build
cache can serve a stale layer if only `runtime/shared/.env` changed (build
args aren't re-evaluated the same way env vars are).

**Fix:**
```bash
docker compose -f runtime/foundation/compose/docker-compose.yaml build --no-cache
bash runtime/foundation/compose/start-compose.sh
```

### 4.5 `stop-compose.sh --volumes` doesn't actually give you a clean slate

**Symptom:** After `--volumes`, `docker volume ls` still shows volumes from
this project, or a fresh `start-compose.sh` behaves like state carried over.

**Cause:** `docker compose down --volumes` only removes volumes *declared in
the current `docker-compose.yaml`*. If a service was removed from the file
without also removing its container and volume (e.g. a past `trino-init`
service, before Trino switched to `tmpfs`), both become orphaned — invisible
to Compose, never cleaned by `--volumes`, silently persisting across every
"reset." Confirmed live on 2026-08-20: `compose_airflow-vendor` and
`compose_trino-data` had survived this way, held by a long-exited
`trino-init` container.

**Fix:**
```bash
docker ps -a --filter "name=compose_" -a   # or just: docker ps -a, look for anything not in docker-compose.yaml
docker volume ls --filter name=compose_
# for anything not declared in docker-compose.yaml's top-level `volumes:`:
docker rm <orphan container>
docker volume rm <orphan volume>
```

### 4.6 `smoke-test.sh` or `validate-config-first.sh` can't find a container

**Symptom:** `docker inspect` errors, or the script reports a container is
"not running (not found)".

**Cause:** The stack isn't up, or a container name changed in
`docker-compose.yaml` without updating these scripts (they reference fixed
`container_name` values: `frankenphp`, `jupyter`, `airflow-scheduler`).

**Fix:** Confirm with `docker compose ps` first; if a name genuinely changed,
the scripts need updating alongside it.

### 4.7 A DAG file you just added doesn't appear in Airflow Web

**Symptom:** `airflow dags list-import-errors` shows nothing, the file is
present on disk inside the container, and `airflow dags list` (CLI) already
shows it — but the Airflow Web UI reports the DAG "missing from DagBag" or
just doesn't list it, and trying to build a direct URL to it fails.

**Cause:** `airflow-web`'s Gunicorn workers each cache their own in-process
view of the DAGs and only refresh it when a worker recycles —
`worker_refresh_interval` (`airflow config get-value webserver
worker_refresh_interval`) defaults to 6000 seconds (100 minutes) in this
stack. The scheduler picks up new DAG files fast (its own
`dag_dir_list_interval` is much shorter, ~30–300s) and serializes them into
the metadata DB right away — confirmable directly:
```bash
docker exec postgres psql -U airflow -d airflow -c \
  "SELECT dag_id, last_updated FROM serialized_dag WHERE dag_id = '<your_dag_id>';"
```
If that query returns a row, the backend already knows about the DAG — it's
purely the webserver's stale in-memory cache blocking the GUI. Live-
reproduced 2026-08-21 adding `asx_ohlcv_curated_from_public_source`.

**Fix:** Restart just the webserver — stateless, safe, no data loss:
```bash
docker compose -f runtime/foundation/compose/docker-compose.yaml restart airflow-web
```

## 5. Shutdown

```bash
bash runtime/foundation/compose/stop-compose.sh            # keeps named volumes (minio-data, postgres-data, etc.)
bash runtime/foundation/compose/stop-compose.sh --volumes   # also deletes them — full reset, next start is a cold start
```

## 6. What's Different From the Kubernetes Stack

Worth knowing if you're moving between the two:

- **No live-mount fragility.** Compose uses plain Docker bind mounts for
  `runtime/shared/*` — there's no Minikube-mount-process equivalent that can
  go stale, and no `subPath` corruption risk. If the host file is right,
  the container sees it, immediately, always.
- **No Job-immutability trap.** `airflow-init`, `minio-init`, and
  `lakekeeper-migrate` are plain one-shot containers Compose recreates
  cleanly on every run. Kubernetes's equivalent Jobs can't be patched in
  place once created (see `docs/runtime/knowledge-lake/TROUBLESHOOTING.md` §4
  if you hit that on the k8s side).
- **Config source is identical.** Both stacks read only from
  `runtime/shared/.env` — no separate Compose-specific credential file.

## 7. Credentials & Access

Full URL + login table lives in
[`runtime/foundation/compose/README.md`](../../../runtime/foundation/compose/README.md#running-a-solution)
(single source of truth, kept next to the commands that start the stack).
Real credentials (MinIO, PostgreSQL, Airflow) all come from the one
centralized file: `runtime/shared/.env` (template at
`runtime/shared/.env.example`).

Compose doesn't run Metabase, Elasticsearch, Kibana, Open WebUI, or the AI
Access API at all — those are Kubernetes-addon-only (see
`docs/runtime/knowledge-lake/TROUBLESHOOTING.md` §9 if you need them).
