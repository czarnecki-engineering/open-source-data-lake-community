# RUNBOOK — Open Data Lake (Community Edition)

## 1. Purpose
Operate the local Docker Compose stack for the Open Data Lake (Community Edition).
Covers start, stop, validation, and basic recovery.

---

## 2. Preconditions
- Docker running
- `docker compose` available
- `.env` file present and complete
- Run commands from repo root

---

## 3. Start Base Stack
```bash
./start-compose.sh
```

Expected:
- Containers start in detached mode

---

## 4. Stop Base Stack
```bash
./stop-compose.sh
```

---

## 5. Reset (Clean State)
```bash
./stop-compose.sh --volumes
```

Optional deeper clean:
```bash
docker system prune -f
docker volume prune -f
```

---

## 6. Verify Successful Start
```bash
docker ps --format '{{.Names}}: {{.Status}}' | sort
```

Expected:
- All core containers are running

Key endpoints (local only):
- Airflow: http://localhost:8080
- MinIO: http://localhost:9001
- Jupyter: http://localhost:8888

---

## 7. Remote / Sandbox Validation
If localhost is not accessible:

```bash
docker compose ps
docker logs airflow-webserver --tail 50
docker logs minio --tail 50
docker logs jupyter --tail 50
```

---

## 8. Logs & Diagnostics
```bash
docker compose logs -f <service>
```

Common services:
- airflow-webserver
- airflow-scheduler
- minio
- jupyter

---

## 9. Common Failure Modes

**Containers not starting**
- Cause: port conflict
- Fix: stop conflicting service

**Airflow UI not accessible**
- Cause: startup delay
- Fix: wait and recheck logs

**MinIO not reachable**
- Cause: container failed
- Fix: check logs, restart stack

**Jupyter token issues**
- Cause: missing/incorrect `.env`
- Fix: verify `JUPYTER_TOKEN`

---

## 10. Command Reference
```bash
./start-compose.sh
./stop-compose.sh
./stop-compose.sh --volumes
docker ps --format '{{.Names}}: {{.Status}}' | sort
docker compose logs -f <service>
```
