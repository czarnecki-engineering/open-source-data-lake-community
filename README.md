# Open Source Data Lake Community

A self-contained, local Open Source Data Lake implementation for demonstrating an end-to-end data-lake workflow with open-source components.

The repository includes the runtime, configuration, pipelines, notebooks, presentation pages, validation scripts, and example workloads required to run the Community solution locally with Docker Compose.

## What It Demonstrates

The Community runtime provides a practical data path from ingestion through storage, transformation, Iceberg publication, query, analysis, and presentation.

Configured runtime components include:

- MinIO — S3-compatible object storage
- PostgreSQL — metadata database
- Lakekeeper — Iceberg REST catalog
- Trino — SQL query engine
- Apache Airflow — pipeline orchestration
- Jupyter — notebook analysis
- FrankenPHP — lightweight presentation layer
- CloudBeaver — database/query client

Two example workloads are included:

- `heartbeat` — a small proving pipeline for validating the complete runtime path
- `asx_ohlcv` — a real-data ASX market-data pipeline and research workflow

## Repository Layout

```text
runtime/
  foundation/compose/   Docker Compose runtime, Dockerfiles and operational scripts
  shared/
    config/             Runtime and workload configuration
    dags/               Airflow DAGs and workload helpers
    data/               Generated local working artifacts
    notebooks/          Jupyter analysis notebooks
    php/                Community presentation pages
    scripts/            Shared runtime scripts
    trino/              Trino configuration

tests/                  Python tests
docs/runtime/compose/   Compose troubleshooting documentation
```

## Prerequisites

- Docker Desktop, or another Docker daemon with Docker Compose v2
- `curl`, `python3`, and `shasum` for the supplied validation scripts
- Python 3 and the listed Python dependencies if you want to run the repository tests locally

## Quick Start

From the repository root, create the local runtime configuration on first use:

```bash
cp runtime/shared/.env.example runtime/shared/.env
```

Start the complete Community runtime:

```bash
bash runtime/foundation/compose/start-compose.sh
```

Validate it:

```bash
bash runtime/foundation/compose/smoke-test.sh
bash runtime/foundation/compose/validate-config-first.sh
```

The Community homepage is then available at:

```text
http://127.0.0.1:8088/index.php
```

For the complete URL/login table and workload execution instructions, see [`runtime/foundation/compose/README.md`](runtime/foundation/compose/README.md).

## Repository Tests

To run the Python tests independently of the runtime:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pandas yfinance scipy pyarrow boto3
python -m unittest discover -s tests -p 'test_*.py'
```

## Included Workloads

### Heartbeat

The heartbeat workload is the minimal end-to-end proving path. Its Airflow DAGs move a generated event through raw, conformed and curated storage before publishing an Iceberg table. The Jupyter notebook reads the published result and writes a local summary consumed by the presentation layer.

### ASX OHLCV

The ASX workload retrieves configured market data from Yahoo Finance, writes source data directly to MinIO, transforms it through conformed and curated stages, publishes Iceberg data, builds sector reference data, and supports the included publication/research notebook.

Detailed execution order is documented in [`runtime/foundation/compose/README.md`](runtime/foundation/compose/README.md).

## Shutdown

Stop the runtime while retaining named-volume data:

```bash
bash runtime/foundation/compose/stop-compose.sh
```

For a destructive reset that also removes the runtime's named volumes:

```bash
bash runtime/foundation/compose/stop-compose.sh --volumes
```

## Documentation

- [Compose runtime guide](runtime/foundation/compose/README.md)
- [Compose troubleshooting](docs/runtime/compose/TROUBLESHOOTING.md)

The runtime configuration and scripts are authoritative where documentation and implementation differ.
