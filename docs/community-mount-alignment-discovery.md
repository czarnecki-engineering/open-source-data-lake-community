# Community Mount Alignment Discovery

## 1. Docker Compose mounts (by service)

Source: [docker-compose.yaml](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:1)

MINIO:
- `minio-data` → `/data` (named volume) ([docker-compose.yaml:14](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:14))

MINIO-INIT:
- No `volumes:` entries present. ([docker-compose.yaml:23](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:23))

AIRFLOW:
- `./dags` → `/opt/airflow/dags` (RW) ([docker-compose.yaml:78](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:78))
- `./logs` → `/opt/airflow/logs` (RW) ([docker-compose.yaml:78](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:78))
- `./plugins` → `/opt/airflow/plugins` (RW) ([docker-compose.yaml:78](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:78))
- `./config` → `/opt/airflow/config` (RO) ([docker-compose.yaml:78](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:78))
- `airflow-db` → `/opt/airflow` (named volume) ([docker-compose.yaml:78](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:78))

JUPYTER:
- `./notebooks` → `/home/jovyan/work` (RW) ([docker-compose.yaml:108](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:108))

PHP:
- `./php` → `/app/public` (RW) ([docker-compose.yaml:117](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:117))

## 2. Host-mounted folders (normalized)

Unique bind-mounted host paths from `docker-compose.yaml`:

- `config/` from `./config` ([docker-compose.yaml:82](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:82))
- `dags/` from `./dags` ([docker-compose.yaml:79](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:79))
- `logs/` from `./logs` ([docker-compose.yaml:80](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:80))
- `notebooks/` from `./notebooks` ([docker-compose.yaml:109](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:109))
- `php/` from `./php` ([docker-compose.yaml:119](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:119))
- `plugins/` from `./plugins` ([docker-compose.yaml:81](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:81))

## 3. Comparison to required model

### 3.1 RW mounts

- `dags/`: `PRESENT_CORRECT` ([docker-compose.yaml:79](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:79))
- `logs/`: `PRESENT_CORRECT` ([docker-compose.yaml:80](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:80))
- `plugins/`: `PRESENT_CORRECT` ([docker-compose.yaml:81](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:81))
- `notebooks/`: `PRESENT_CORRECT` ([docker-compose.yaml:109](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:109))
- `php/`: `PRESENT_CORRECT` ([docker-compose.yaml:119](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:119))

### 3.2 RO mounts

- `config/`: `PRESENT_CORRECT` ([docker-compose.yaml:82](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:82))

### 3.3 Extra mounts

- No extra bind-mounted host paths were identified beyond `dags/`, `logs/`, `plugins/`, `notebooks/`, `php/`, and `config/`. ([docker-compose.yaml:78](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:78))

## 4. Named volume validation

- MinIO data: `PRESENT` via `minio-data:/data`, with `minio-data` declared under top-level `volumes:`. ([docker-compose.yaml:14](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:14), [docker-compose.yaml:125](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:125))
- Airflow DB: `PRESENT` via `airflow-db:/opt/airflow`, with `airflow-db` declared under top-level `volumes:`; Airflow sets `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN` to `sqlite:////opt/airflow/airflow.db`, which places the database file under the named volume mount point. ([docker-compose.yaml:56](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:56), [docker-compose.yaml:83](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:83), [docker-compose.yaml:125](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:125))

## 5. Service mapping

- `dags/` → `airflow`: confirmed by `./dags:/opt/airflow/dags`. ([docker-compose.yaml:79](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:79))
- `logs/` → `airflow`: confirmed by `./logs:/opt/airflow/logs`. ([docker-compose.yaml:80](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:80))
- `plugins/` → `airflow`: confirmed by `./plugins:/opt/airflow/plugins`. ([docker-compose.yaml:81](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:81))
- `notebooks/` → `jupyter`: confirmed by `./notebooks:/home/jovyan/work`. ([docker-compose.yaml:109](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:109))
- `php/` → `php`: confirmed by `./php:/app/public`. ([docker-compose.yaml:119](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:119))
- `config/` → `airflow` (RO): confirmed by `./config:/opt/airflow/config:ro`. ([docker-compose.yaml:82](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:82))
- MinIO named volume → `minio`: confirmed by `minio-data:/data`. ([docker-compose.yaml:15](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:15))
- Airflow named volume → `airflow`: confirmed by `airflow-db:/opt/airflow`. ([docker-compose.yaml:83](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:83))

## 6. Deviations from model

- No source-backed deviations from the required mount model were identified in `docker-compose.yaml`. ([docker-compose.yaml:78](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:78), [docker-compose.yaml:108](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:108), [docker-compose.yaml:117](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:117), [docker-compose.yaml:125](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:125))

## 7. Risks (only real issues)

- `stop-compose.sh --volumes` runs `docker compose down -v`, which removes compose volumes; this would remove the named volumes used for MinIO data and the Airflow DB. ([stop-compose.sh:43](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/stop-compose.sh:43), [docker-compose.yaml:15](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:15), [docker-compose.yaml:83](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:83))
- No source-backed mount misalignment was identified that would cause DAGs not loading, config not being readable, or logs not being writable under the declared compose configuration. ([docker-compose.yaml:79](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:79), [docker-compose.yaml:80](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:80), [docker-compose.yaml:82](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:82))

## 8. Appendix: files inspected

Mandatory files inspected:

- [docker-compose.yaml](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:1)
- [start-compose.sh](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/start-compose.sh:1)
- [stop-compose.sh](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/stop-compose.sh:1)

Referenced env files / additional files checked:

- No additional `docker-compose.*.yaml` files were present in the repository root. Verified by repository file listing.
- `.env` is mentioned in `start-compose.sh` as a possible override source for access URLs, but no `env_file:` directive is present in `docker-compose.yaml`. ([start-compose.sh:46](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/start-compose.sh:46), [docker-compose.yaml:1](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml:1))
- [.env.example](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/.env.example:1) was inspected as the only env template file present in the repository root.
