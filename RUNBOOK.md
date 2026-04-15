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

## Canonical Local Commands

Use the repository wrapper scripts as the canonical local entry points.

### Start the stack

```bash
./start-compose.sh
```

What it does:

* runs `docker compose build`
* runs `docker compose up -d`
* prints the default local access URLs

Use this for normal local startup from the repository root.

### Normal stop

```bash
./stop-compose.sh
```

What it does:

* runs `docker compose down`
* stops and removes the stack containers
* preserves Docker volumes and their data

Use this for routine shutdown when you want to keep local state.

### Stop and remove volumes

```bash
./stop-compose.sh --volumes
```

What it does:

* runs `docker compose down -v`
* stops and removes the stack containers
* removes the stack's Docker volumes

Use this only when you want a clean local reset of persisted stack state.

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

Stateful runtime data is split between **Docker volumes** and **bind-mounted repository folders**.

---

## Reset Modes

Choose the stop mode based on whether you want to preserve or clear persisted state.

### Normal stop

```bash
./stop-compose.sh
```

Effect:

* containers stop
* Compose removes the containers and network
* Docker volumes are preserved

Data preserved:

* MinIO bucket contents in volume `minio-data`
* Airflow metadata in volume `airflow-db`
* repository files and bind-mounted directories such as `config/`, `dags/`, `notebooks/`, `php/`, `logs/`, and `plugins/`

Typical use:

* end of day shutdown
* restart later without losing Airflow history or MinIO objects

### Full reset

```bash
./stop-compose.sh --volumes
```

Effect:

* containers stop
* Compose removes the containers and network
* Compose removes the stack Docker volumes

Data deleted:

* MinIO bucket contents in `minio-data`
* Airflow metadata database in `airflow-db`

Data retained:

* repository files and bind-mounted directories such as `config/`, `dags/`, `notebooks/`, `php/`, `logs/`, and `plugins/`
* local configuration files such as `config/asx200_tickers.csv`

Typical use:

* reset a demo environment
* clear stale local state before reproducing a run from scratch

---

## Data Persistence

This stack does not persist all data in the same place. Operationally, the important split is:

| Location | Purpose | Removed by `./stop-compose.sh` | Removed by `./stop-compose.sh --volumes` |
| --------------- | -------------- | -------------- | -------------- |
| `minio-data` Docker volume | MinIO buckets and objects | No | Yes |
| `airflow-db` Docker volume | Airflow SQLite metadata DB and scheduler state | No | Yes |
| `./notebooks` bind mount | Notebook files in the repo working tree | No | No |
| `./php` bind mount | PHP service files in the repo working tree | No | No |
| `./dags` bind mount | DAG source files in the repo working tree | No | No |
| `./config` bind mount | Local operator config including `asx200_tickers.csv` | No | No |
| `./logs` bind mount | Airflow logs on the host | No | No |
| `./plugins` bind mount | Airflow plugin files on the host | No | No |

Practical implication:

* if you want to keep MinIO objects and Airflow history, use `./stop-compose.sh`
* if you want to clear MinIO objects and Airflow history, use `./stop-compose.sh --volumes`
* neither stop mode deletes Git-tracked repository content

---

## Clean Teardown (Reset to Zero)

Use this sequence when preparing a clean demo, Medium article, or reproducibility test.

### 1. Stop containers and remove volumes (critical)

```bash
./stop-compose.sh --volumes
```

This removes:

* Airflow metadata database
* MinIO object storage (all buckets and objects)
* Named and anonymous volumes attached to the stack

It does **not** remove notebook files stored in the bind-mounted `./notebooks` directory.

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
./start-compose.sh
```

This canonical command:

* builds the custom Airflow image
* builds the custom Jupyter image
* starts the stack in detached mode

---

### 2. Verify container health

```bash
docker ps --format '{{.Names}}: {{.Status}}' | sort
```

You should see containers for:

* airflow
* minio
* jupyter
* supporting services (scheduler, webserver, etc.)

---

## Manual Ticker Configuration (ASX Data Pipeline)

* The ASX ingestion DAG `asx200_ohlcv_daily_to_raw` requires a local configuration file:
  `config/asx200_tickers.csv`
* This file is not provided by default and must be created manually by the operator.
* Purpose:
  control the number of tickers queried from yFinance and avoid excessive or abusive API usage.
* Behaviour:
  * if the file is missing, the DAG will fail
  * this is expected and does not indicate a problem with the platform
* The platform is considered healthy if:
  * services start successfully
  * the Airflow UI is accessible
  * heartbeat DAGs are running
* Sample starting points:
  * `config/asx200_tickers_top3.csv`
  * `config/asx200_tickers_top100.csv`

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
| Jupyter notebooks | Git-tracked bind mount |
| DAGs            | Git-tracked    |
| Notebooks       | Git-tracked    |

A full reset with `./stop-compose.sh --volumes` destroys data held in the stack Docker volumes, but not files that remain in bind-mounted repository folders.

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
