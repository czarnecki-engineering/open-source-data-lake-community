# Open Source Data Lake – Community Edition

This repository provides a Docker Compose–based reference implementation of an
Open Source Data Lake using:

- MinIO (object storage)
- Apache Airflow (orchestration)
- Jupyter (EDA and data science)

## Target users

- **Data Engineers**
  - Airflow DAGs
  - Medallion architecture (raw → conformed → curated)
  - Object storage with MinIO

- **Data Scientists**
  - Jupyter notebooks
  - Exploratory Data Analysis on curated datasets

## Architecture

- Docker Compose–based local deployment
- Three-layer medallion data lake
- Scheduled heartbeat pipeline
- Market data ingestion (ASX)

This repository is the canonical **Community Edition** and serves as the
foundation for higher tiers (Supported, Cloud, Enterprise).
