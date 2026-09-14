# Community Compose Troubleshooting

Use this page for specific Docker Compose runtime failures. For startup instructions, URLs and credentials, see [`runtime/foundation/compose/README.md`](../../../runtime/foundation/compose/README.md).

Before diagnosing a specific problem, check the current service state:

```bash
docker compose -f runtime/foundation/compose/docker-compose.yaml ps
```

## Port already in use

**Symptom**

`start-compose.sh` fails immediately, or Docker Compose reports that a host port is already allocated.

**Check**

Identify the process using the reported port. For example:

```bash
lsof -nP -iTCP:8088 -sTCP:LISTEN
```

**Fix**

Stop the conflicting process, or change the corresponding port in `runtime/shared/.env`.

## Airflow remains in `health: starting`

**Symptom**

`airflow-web` or `airflow-scheduler` remains in `health: starting` after startup.

**Check**

For the web service:

```bash
docker inspect --format '{{.State.Health.Status}}' airflow-web
docker logs airflow-web --tail=50
```

**Fix**

Initial Airflow startup can take time. If the service does not become healthy, use the log output to identify the failing dependency or configuration before restarting the affected service.

## `Found orphan containers` warning

**Symptom**

Docker Compose reports orphan containers left by an earlier runtime definition.

**Check**

Confirm the warning refers to containers no longer present in the current Compose file.

**Fix**

```bash
docker compose -f runtime/foundation/compose/docker-compose.yaml up -d --remove-orphans
```

## Dockerfile or dependency changes are not reflected

**Symptom**

A Dockerfile or image dependency was changed, but the running service still behaves like the old image.

**Check**

Confirm the affected service is built from the local Dockerfile rather than using only a published image.

**Fix**

Rebuild without Docker's layer cache, then restart:

```bash
docker compose -f runtime/foundation/compose/docker-compose.yaml build --no-cache
bash runtime/foundation/compose/start-compose.sh
```

## Full reset leaves old containers or volumes

**Symptom**

`stop-compose.sh --volumes` completes, but obsolete containers or volumes from an older runtime definition remain.

**Check**

```bash
docker ps -a
docker volume ls
```

**Fix**

Remove only objects you have positively identified as obsolete:

```bash
docker rm <orphan-container>
docker volume rm <orphan-volume>
```

These commands are destructive. Do not remove unidentified containers or volumes.

## Validation cannot find an expected container

**Symptom**

`smoke-test.sh` or `validate-config-first.sh` reports that an expected container is missing or not running.

**Check**

```bash
docker compose -f runtime/foundation/compose/docker-compose.yaml ps
```

Then inspect the affected service:

```bash
docker compose -f runtime/foundation/compose/docker-compose.yaml logs <service> --tail=100
```

**Fix**

Resolve the service startup failure first, then rerun the validation script. If the runtime is healthy but validation still references a missing container, treat that as an implementation/validation mismatch.

## DAG does not appear in Airflow Web

**Symptom**

A newly added DAG is mounted and available to Airflow, but does not appear in the web UI.

**Check**

Confirm the DAG has no import error and is visible to the scheduler or Airflow CLI.

**Fix**

If the scheduler has loaded the DAG but the web UI remains stale, restart only the web service:

```bash
docker compose -f runtime/foundation/compose/docker-compose.yaml restart airflow-web
```

This does not reset the rest of the Community runtime.
