# RUNBOOK — Open Source Data Lake (Community Edition)

This runbook describes how to **cleanly tear down**, **rebuild**, and **operate** the Open Source Data Lake – Community Edition using Docker Compose.

It is intended to support:

* reproducible local deployments,
* end-to-end demonstrations,
* Medium walkthroughs,
* and onboarding of contributors or readers.

---

## Scope

This runbook covers the local Docker Compose stack consisting of:

* **MinIO** — object storage (raw / conformed / curated zones)
* **Apache Airflow** — orchestration and ingestion
* **Jupyter** — EDA and data science notebooks

It applies to the **Community Edition** only.

---

## Preconditions

* Docker Engine installed and running
* Docker Compose v2 (`docker compose`) available
* You are in the repository root directory
  (the folder containing `docker-compose.yaml`)

Optional sanity check:

```bash
docker ps --format '{{.Names}}: {{.Status}}' | sort
```

---

## Project Structure (Operational View)

```
.
├── docker-compose.yaml
├── docker/
│   ├── airflow/
│   │   └── Dockerfile
│   └── jupyter/
│       └── Dockerfile
├── dags/
├── notebooks/
│   └── eda_output/    # runtime (recreated by notebooks)
├── logs/              # runtime (recreated on startup)
└── RUNBOOK.md
```

Stateful runtime data is held in **Docker volumes**, not in the repository.

---

## Clean Teardown (Reset to Zero)

Use this sequence when preparing a clean demo, Medium article, or reproducibility test.

### 1. Stop containers and remove volumes (critical)

```bash
docker compose down -v
```

This removes:

* Airflow metadata database
* MinIO object storage (all buckets and objects)
* Jupyter runtime state
* Named and anonymous volumes attached to the stack

---

### 2. Remove custom images built by this project

(Optional but recommended for a true clean build.)

List relevant images:

```bash
docker images | grep -E 'airflow|jupyter'
```

Remove them:

```bash
docker image rm airflow-custom:latest jupyter-minimal-notebook:custom 2>/dev/null
```

Image names may vary slightly depending on local tagging.

---

### 3. Prune dangling Docker artefacts

```bash
docker system prune -f
docker volume prune -f
docker network prune -f
```

This removes unused artefacts without affecting other active projects.

---

### 4. Clean host-side runtime directories

These directories hold generated artefacts and should not be reused for a clean run.

#### macOS / Linux

```bash
rm -rf logs eda_output .ipynb_checkpoints
```

#### Windows (PowerShell)

```powershell
Remove-Item -Recurse -Force .\logs 2>$null
Remove-Item -Recurse -Force .\eda_output 2>$null
Remove-Item -Recurse -Force .\.ipynb_checkpoints 2>$null
```

Do **not** delete:

* `docker/`
* `dags/`
* `notebooks/`
* `docker-compose.yaml`

---

### 5. Verify clean state

```bash
docker ps --format '{{.Names}}: {{.Status}}' | sort
```

No containers from this project should be running.

---

## Clean Build and Startup

This is the **canonical startup sequence**.

### 1. Build images

```bash
docker compose build
```

This builds:

* the custom Airflow image
* the custom Jupyter image with baked-in data science libraries

---

### 2. Start the stack

```bash
docker compose up -d
```

---

### 3. Verify container health

```bash
docker ps --format '{{.Names}}: {{.Status}}' | sort
```

You should see containers for:

* airflow
* minio
* jupyter
* supporting services (scheduler, webserver, etc.)

---

## Service Access

### Airflow

* URL: `http://localhost:8080`
* Purpose: ingestion, orchestration, DAG execution

### MinIO

* URL: `http://localhost:9001`
* Purpose: object storage (raw / conformed / curated)
* Credentials: as defined in `docker-compose.yaml`

### Jupyter

* URL: `http://localhost:8888`
* Purpose: EDA and data science notebooks
* Token: as defined in `docker-compose.yaml`

---

## Operational Notes

### Stateless vs Stateful Components

| Component       | State location |
| --------------- | -------------- |
| Airflow         | Docker volumes |
| MinIO           | Docker volumes |
| Jupyter runtime | Docker volumes |
| DAGs            | Git-tracked    |
| Notebooks       | Git-tracked    |

A full teardown (`docker compose down -v`) **destroys all data**.

---

### Reproducibility Guarantee

If the runbook steps are followed exactly:

* the environment is deterministic,
* no hidden state persists,
* results can be reproduced by third parties.

This is intentional and foundational to the Community Edition.

---

## Intended Usage

This runbook supports:

* Medium walkthroughs (“from zero to running data lake”)
* Local experimentation
* Teaching and demonstration
* Foundation for Supported / Cloud / Enterprise tiers
