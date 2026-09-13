# Community Compose Runtime Troubleshooting

Operational troubleshooting for the Open Source Data Lake Community Docker Compose runtime.

## 1. Before You Debug Anything

Confirm the basic runtime prerequisites first:

- Run commands from the **repository root**.
- **Docker Desktop** or another Docker daemon is running (`docker info` succeeds).
- Docker Compose v2 is available (`docker compose version` succeeds).
- **`runtime/shared/.env` exists** if you want to use local configuration rather than the defaults available in the Compose definition:

```bash
cp runtime/shared/.env.example runtime/shared/.env
```

- Nothing else is bound to the Community runtime's configured host ports.

## 2. Golden Startup Path

```bash
bash runtime/foundation/compose/start-compose.sh
bash runtime/foundation/compose/smoke-test.sh
bash runtime/foundation/compose/validate-config-first.sh
```

Then open:

```text
http://127.0.0.1:8088/index.php
```

## 3. Mandatory First Checks

```bash
docker compose -f runtime/foundation/compose/docker-compose.yaml ps
```

Long-running services should show as running. One-shot initialisation or migration containers may show `Exited (0)` after successful completion; that is expected.

## 4. Known Failure Modes And Fixes

### 4.1 Port already in use

**Symptom:** `start-compose.sh` fails immediately, or Docker Compose reports that a port is already allocated.

**Cause:** Another local process or container is already listening on one of the configured host ports.

**Fix:** Identify the process using the affected port. For example:

```bash
lsof -nP -iTCP:8088 -sTCP:LISTEN
```

Stop the conflicting process or change the corresponding port in `runtime/shared/.env`.

### 4.2 `airflow-web` / `airflow-scheduler` show `health: starting` for a while

This can be expected during first boot. Give the services time to initialise and then recheck:

```bash
docker inspect --format '{{.State.Health.Status}}' airflow-web
```

If the service still does not become healthy, inspect its logs:

```bash
docker logs airflow-web --tail=50
```

### 4.3 `Found orphan containers` warning on startup

**Symptom:** Docker Compose warns about orphan containers left by an earlier version of the Compose definition.

This does not necessarily indicate a failure in the current runtime. To remove containers no longer defined by the current Compose file:

```bash
docker compose -f runtime/foundation/compose/docker-compose.yaml up -d --remove-orphans
```

### 4.4 Dockerfile or dependency changes do not take effect

**Cause:** Docker's build cache may reuse an existing image layer.

**Fix:** Rebuild without the cache, then restart the runtime:

```bash
docker compose -f runtime/foundation/compose/docker-compose.yaml build --no-cache
bash runtime/foundation/compose/start-compose.sh
```

### 4.5 `stop-compose.sh --volumes` does not give you a clean slate

`docker compose down --volumes` removes volumes declared by the current Compose definition. Containers or volumes orphaned by older versions of the runtime may remain outside the current Compose model.

Inspect them with:

```bash
docker ps -a
docker volume ls
```

If you identify an obsolete container or volume from an older Community runtime definition, remove it explicitly:

```bash
docker rm <orphan-container>
docker volume rm <orphan-volume>
```

These commands are destructive. Remove only objects you have identified as obsolete.

### 4.6 `smoke-test.sh` or `validate-config-first.sh` cannot find a container

**Symptom:** `docker inspect` errors, or a validation script reports that an expected container is not running or cannot be found.

**Cause:** The runtime did not start successfully, or the implementation and validation script have become inconsistent.

**Fix:** Start with:

```bash
docker compose -f runtime/foundation/compose/docker-compose.yaml ps
```

Then inspect the logs of the affected service before rerunning validation.

### 4.7 A newly added DAG does not appear in Airflow Web

**Symptom:** The DAG file is mounted correctly and may already be visible to the scheduler or CLI, but it does not appear in the Airflow Web UI.

The webserver can retain a stale in-process DAG view. First confirm that the DAG has no import error and is visible to Airflow. If the scheduler has loaded it but the web UI has not refreshed, restart only the webserver:

```bash
docker compose -f runtime/foundation/compose/docker-compose.yaml restart airflow-web
```

This restarts the Airflow web service without resetting the Community data-lake runtime.

## 5. Shutdown

Normal shutdown retains named-volume data:

```bash
bash runtime/foundation/compose/stop-compose.sh
```

A full reset also removes the named volumes managed by the current Compose definition:

```bash
bash runtime/foundation/compose/stop-compose.sh --volumes
```

Use the second form only when you intend to remove persisted local runtime state.

## 6. Credentials And Access

The complete URL and login table is maintained in [`runtime/foundation/compose/README.md`](../../../runtime/foundation/compose/README.md#local-urls-and-logins).

Local runtime configuration is read from `runtime/shared/.env`; the tracked starting template is `runtime/shared/.env.example`.
