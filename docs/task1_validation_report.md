# Task 1 Validation Report
- Repo: open-source-data-lake-community
- Mode: Execution
- Generated: 2026-04-16 20:57:48 AEST

## Execution Notes

- GUI AUTOMATION NOT AVAILABLE in this Codex environment.
- Validation will use non-GUI fallback methods where browser interaction cannot be performed.
- No application source code was modified during this execution.

## Phase 1 - Clean Reset

Command:

```bash
./stop-compose.sh --volumes
```

Output:

```text
Stopping stack and removing volumes (docker compose down -v)...
time="2026-04-16T20:59:00+10:00" level=warning msg="/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docker-compose.yaml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion"
 Volume open-source-data-lake-community_airflow-db  Removing
 Volume open-source-data-lake-community_minio-data  Removing
 Volume open-source-data-lake-community_airflow-db  Removed
 Volume open-source-data-lake-community_minio-data  Removed
```

Command:

```bash
docker ps --format '{{.Names}}: {{.Status}}' | sort
```

Output:

```text
[no output]
```

Result:

- Project containers gone: YES
- Notes:
  - Initial sandboxed Docker access failed because the Docker daemon was not available, then Docker Desktop was launched and Docker commands were rerun with elevated permissions to reach the host daemon.
  - The compose warning about obsolete `version` was observed but did not block reset.

## Phase 2 - Prepare ASX Config

Initial check:

```bash
test -f ./config/asx200_tickers.csv && echo EXISTS || echo MISSING
```

Output:

```text
MISSING
```

Evidence reviewed:

- `config/README.md` documents that `config/asx200_tickers.csv` must be created manually and lists `config/asx200_tickers_top3.csv` and `config/asx200_tickers_top100.csv` as sample starting points.
- `README.md` also lists `config/asx200_tickers_top3.csv` and `config/asx200_tickers_top100.csv` as examples.

Action:

```bash
cp ./config/asx200_tickers_top3.csv ./config/asx200_tickers.csv
```

Recorded output:

```text
copied=config/asx200_tickers_top3.csv -> config/asx200_tickers.csv
ticker
CBA
BHP
RIO
```

Result:

- `config/asx200_tickers.csv` created: YES
- Source file copied: `config/asx200_tickers_top3.csv`
- Notes:
  - `config/asx200_tickers_top3.csv` was selected because it is a documented sample starting point and is the smallest provided sample, reducing external yFinance load during validation.

## Phase 3 - Start Stack

Command:

```bash
./start-compose.sh
```

Output summary:

```text
Building images (docker compose build)...
apache/airflow:2.10.3-custom  Built
jupyter/minimal-notebook:custom  Built
Starting stack (docker compose up -d)...
Network open-source-data-lake-community_default  Created
Volume open-source-data-lake-community_minio-data  Created
Volume open-source-data-lake-community_airflow-db  Created
Container minio  Started
Container jupyter  Started
Container php  Started
Container minio-init  Started
Container minio-init  Exited
Container airflow  Started
```

Startup script note:

```text
Stack is starting. Default access URLs (may differ if overridden via .env):
- Airflow:        http://localhost:8080
- MinIO Console:  http://localhost:9001
- MinIO API:      http://localhost:9000
- Jupyter:        http://localhost:8888
- PHP:            http://localhost:8088
```

First post-start command:

```bash
docker ps --format '{{.Names}}: {{.Status}}' | sort
```

Initial output:

```text
airflow: Up 12 seconds (health: starting)
jupyter: Up 19 seconds (healthy)
minio: Up 19 seconds (healthy)
php: Up 19 seconds (health: starting)
```

Final output after validation:

```text
airflow: Up 7 minutes (healthy)
jupyter: Up 8 minutes (healthy)
minio: Up 8 minutes (healthy)
php: Up 8 minutes (healthy)
```

Result:

- Services appear healthy: YES
- Obvious startup failures: NO
- Notes:
  - `minio-init` exited normally after bucket initialization.
  - The compose warning about obsolete `version` was observed during build/start and did not block startup.

## Phase 4 - GUI Login / Access Validation

GUI automation status:

- GUI AUTOMATION NOT AVAILABLE in this Codex environment.
- All checks below used fallback methods: `curl`, service APIs, Airflow CLI, and container-assisted MinIO/Jupyter access.

### PHP index

- Reachable: YES
- GUI page loaded: NOT AVAILABLE
- Login attempted: NO
- Login succeeded: NOT VERIFIED
- Notes:
  - `curl -sS -D - http://localhost:8088/` returned `HTTP/1.1 200 OK`.
  - Response body title: `My Data Lake - Services`.
  - Service links were visible in HTML for Airflow, Jupyter, MinIO Console, and MinIO S3 API.
  - Visible link snippet:

```text
<td><strong>Airflow</strong></td> -> http://127.0.0.1:8080/
<td><strong>Jupyter</strong></td> -> http://127.0.0.1:8888/
<td><strong>MinIO Console</strong></td> -> http://127.0.0.1:9001/
<td><strong>MinIO S3 API</strong></td> -> http://127.0.0.1:9000/
```

### MinIO Console

- Reachable: YES
- GUI page loaded: NOT AVAILABLE
- Login attempted: YES
- Login succeeded: YES
- Notes:
  - `curl -sS -D - http://localhost:9001/` returned `HTTP/1.1 200 OK` with `Server: MinIO Console`.
  - Console HTML shell was reachable.
  - Because GUI automation was unavailable, login was validated by credentialed S3 access using repo-evidenced credentials `minioadmin / minioadmin`.
  - Container-assisted MinIO check via boto3 listed buckets `conformed`, `curated`, and `raw`, proving authenticated access.

### Jupyter

- Reachable: YES
- GUI page loaded: NOT AVAILABLE
- Login attempted: YES
- Login succeeded: YES
- Notes:
  - `curl -sS -D - 'http://localhost:8888/?token=jupyter'` returned `HTTP/1.1 302 Found` with `Location: /lab?token=jupyter`.
  - `curl -sS 'http://localhost:8888/api/contents?token=jupyter'` returned the notebook root, and `curl -sS 'http://localhost:8888/api/contents/work?token=jupyter'` listed notebooks under the mounted `work/` directory.
  - Visible notebooks via API:
    - `hello_world.ipynb`
    - `read_heartbeat.ipynb`
    - `read_ohlcv_daily.ipynb`
    - `01_asx_eda.ipynb`
    - `02_asx_preprocessing.ipynb`

### Airflow

- Reachable: YES
- GUI page loaded: NOT AVAILABLE
- Login attempted: YES
- Login succeeded: YES
- Notes:
  - `curl -sS -L -D - http://localhost:8080/home` reached the Airflow sign-in page with title `Sign In - Airflow`.
  - Repo evidence for credentials:
    - `README.md` says Airflow user/password are both `minioadmin`.
    - `docker-compose.yaml` defaults `AIRFLOW_ADMIN_USERNAME` and `AIRFLOW_ADMIN_PASSWORD` to `minioadmin`.
  - HTTP form login with `minioadmin / minioadmin` succeeded.
  - Subsequent authenticated `GET /home` returned `HTTP/1.1 200 OK` with page title `DAGs - Airflow`.
  - Airflow CLI also listed the expected DAGs in the running container.

## Phase 5 - Verify Initial Lake Structure

Evidence:

1. MinIO init container logs:

```text
Waiting for MinIO...
Added `local` successfully.
Bucket created successfully `local/conformed`.
Bucket created successfully `local/raw`.
Bucket created successfully `local/curated`.
[2026-04-16 11:00:20 UTC]     0B conformed/
[2026-04-16 11:00:20 UTC]     0B curated/
[2026-04-16 11:00:20 UTC]     0B raw/
MinIO buckets initialised
```

2. Credentialed boto3 listing from the Airflow container:

```json
{
  "buckets": [
    "conformed",
    "curated",
    "raw"
  ]
}
```

Result:

- `raw` exists: YES
- `conformed` exists: YES
- `curated` exists: YES
- Method: MinIO init logs plus credentialed S3 API access via boto3 from the running Airflow container.

## Phase 6 - Heartbeat Pipeline Validation

Airflow DAG presence:

- `heartbeat_1m_to_raw`: PRESENT
- `heartbeat_1m_copy_raw_to_conformed`: PRESENT
- `heartbeat_1m_copy_conformed_to_curated`: PRESENT

Evidence:

1. `docker exec airflow airflow dags list` included all three heartbeat DAGs.

2. Recent Airflow runs:

```text
heartbeat_1m_to_raw | scheduled__2026-04-16T11:02:00+00:00 | success
heartbeat_1m_to_raw | scheduled__2026-04-16T11:01:00+00:00 | success
heartbeat_1m_to_raw | scheduled__2026-04-16T11:00:00+00:00 | success

heartbeat_1m_copy_raw_to_conformed | scheduled__2026-04-16T11:03:00+00:00 | success
heartbeat_1m_copy_raw_to_conformed | scheduled__2026-04-16T11:02:00+00:00 | success
heartbeat_1m_copy_raw_to_conformed | scheduled__2026-04-16T11:01:00+00:00 | success

heartbeat_1m_copy_conformed_to_curated | scheduled__2026-04-16T11:03:00+00:00 | success
heartbeat_1m_copy_conformed_to_curated | scheduled__2026-04-16T11:02:00+00:00 | success
heartbeat_1m_copy_conformed_to_curated | scheduled__2026-04-16T11:01:00+00:00 | success
```

3. Airflow logs showed successful task completion for the heartbeat chain and repeated scheduled runs.

4. Heartbeat objects observed in MinIO:

```json
{
  "raw": [
    "heartbeat/airflow_time_20260416_210059.txt",
    "heartbeat/airflow_time_20260416_210106.txt",
    "heartbeat/airflow_time_20260416_210213.txt",
    "heartbeat/airflow_time_20260416_210304.txt",
    "heartbeat/airflow_time_20260416_210414.txt",
    "heartbeat/airflow_time_20260416_210509.txt"
  ],
  "conformed": [
    "heartbeat/airflow_time_20260416_210059.txt",
    "heartbeat/airflow_time_20260416_210106.txt",
    "heartbeat/airflow_time_20260416_210213.txt",
    "heartbeat/airflow_time_20260416_210304.txt",
    "heartbeat/airflow_time_20260416_210414.txt"
  ],
  "curated": [
    "heartbeat/airflow_time_20260416_210059.txt",
    "heartbeat/airflow_time_20260416_210106.txt",
    "heartbeat/airflow_time_20260416_210213.txt",
    "heartbeat/airflow_time_20260416_210304.txt",
    "heartbeat/airflow_time_20260416_210414.txt"
  ]
}
```

Result:

- Raw heartbeat objects present: YES
- Conformed heartbeat objects present: YES
- Curated heartbeat objects present: YES
- End-to-end heartbeat propagation confirmed: YES
- Notes:
  - Sampling at one point showed curated lagging one scheduler cycle behind raw/conformed; a later sample confirmed propagation into all three layers.

## Phase 7 - Notebook Validation (Simple / Deterministic)

Access method:

- Jupyter token/API fallback (`?token=jupyter`, Jupyter contents API) plus container-local execution.

Execution method:

- `docker exec jupyter jupyter nbconvert --execute --to notebook --output /tmp/<name>.executed.ipynb /home/jovyan/work/<name>.ipynb`

### `notebooks/hello_world.ipynb`

- Accessed: YES
- Executed: YES
- Success: YES
- Output evidence:

```text
Hello World!
```

### `notebooks/read_heartbeat.ipynb`

- Accessed: YES
- Executed: YES
- Success: YES
- Output evidence:

```text
Heartbeat files:
heartbeat/airflow_time_20260416_210059.txt
heartbeat/airflow_time_20260416_210106.txt
heartbeat/airflow_time_20260416_210213.txt
heartbeat/airflow_time_20260416_210304.txt
heartbeat/airflow_time_20260416_210414.txt

Latest file: heartbeat/airflow_time_20260416_210414.txt
Last modified: 2026-04-16 11:04:14.014000+00:00

File contents:
2026-04-16 21:04:14 AEST
```

Notes:

- Both notebooks executed successfully without modifying repo files; executed outputs were written to container `/tmp`.
- Notebook cells include `pip install` checks that reported packages were already satisfied.

## Phase 8 - ASX Pipeline Validation

Trigger method:

- Airflow CLI fallback in the running container (`docker exec airflow airflow dags trigger ...`).

Initial ASX object state before triggers:

```json
{
  "raw": { "count": 0, "sample": [] },
  "conformed": { "count": 0, "sample": [] },
  "curated": { "count": 0, "sample": [] }
}
```

### 1. `asx200_ohlcv_daily_to_raw`

Trigger result:

```text
manual__2026-04-16T11:05:46+00:00 | queued -> success
```

Run evidence:

```text
asx200_ohlcv_daily_to_raw | manual__2026-04-16T11:05:46+00:00 | success | start 2026-04-16T11:05:47.492975+00:00 | end 2026-04-16T11:05:55.342764+00:00
```

Raw object evidence:

```json
{
  "count": 90,
  "sample": [
    "tabular/market_ohlcv_daily/exchange=ASX/trade_date=2026-03-04/ticker=BHP.csv",
    "tabular/market_ohlcv_daily/exchange=ASX/trade_date=2026-03-04/ticker=CBA.csv",
    "tabular/market_ohlcv_daily/exchange=ASX/trade_date=2026-03-04/ticker=RIO.csv"
  ]
}
```

### 2. `asx200_ohlcv_raw_to_conformed_parquet`

Trigger result:

```text
manual__2026-04-16T11:06:41+00:00 | queued -> success
```

Run evidence:

```text
asx200_ohlcv_raw_to_conformed_parquet | manual__2026-04-16T11:06:41+00:00 | success | start 2026-04-16T11:06:42.618592+00:00 | end 2026-04-16T11:06:49.547076+00:00
```

Conformed object evidence:

```json
{
  "count": 90,
  "sample": [
    "tabular/market_ohlcv_daily/exchange=ASX/trade_date=2026-03-04/ticker=BHP.parquet",
    "tabular/market_ohlcv_daily/exchange=ASX/trade_date=2026-03-04/ticker=CBA.parquet",
    "tabular/market_ohlcv_daily/exchange=ASX/trade_date=2026-03-04/ticker=RIO.parquet"
  ]
}
```

### 3. `asx200_ohlcv_conformed_to_curated_snapshot_v2`

Trigger result:

```text
manual__2026-04-16T11:07:19+00:00 | queued -> success
```

Run evidence:

```text
asx200_ohlcv_conformed_to_curated_snapshot_v2 | manual__2026-04-16T11:07:19+00:00 | success | start 2026-04-16T11:07:20.712973+00:00 | end 2026-04-16T11:07:27.017003+00:00
```

Curated object evidence:

```json
{
  "count": 30,
  "sample": [
    "tabular/market_ohlcv_daily/exchange=ASX/trade_date=2026-03-04/snapshot.parquet",
    "tabular/market_ohlcv_daily/exchange=ASX/trade_date=2026-03-05/snapshot.parquet",
    "tabular/market_ohlcv_daily/exchange=ASX/trade_date=2026-03-06/snapshot.parquet"
  ]
}
```

Result:

- Trigger method worked: YES
- Raw data reached `raw`: YES
- Parquet data reached `conformed`: YES
- Snapshot data reached `curated`: YES
- External dependency issues observed: NO
- Notes:
  - The configured ticker file contained 3 tickers (`CBA`, `BHP`, `RIO`).
  - Resulting object counts were consistent with 30 trade dates x 3 tickers = 90 raw CSV and 90 conformed parquet objects, plus 30 curated snapshot parquet objects.

## Phase 9 - ASX Notebook Validation

Primary notebook:

- `notebooks/read_ohlcv_daily.ipynb`

Access method:

- Jupyter contents API plus container-local execution.

Execution method:

- `docker exec jupyter jupyter nbconvert --execute --to notebook --output /tmp/read_ohlcv_daily.executed.ipynb /home/jovyan/work/read_ohlcv_daily.ipynb`

Result:

- Accessed: YES
- Executed: YES
- Success: YES
- Data availability confirmed: YES

Output evidence:

```text
Found 30 parquet files under s3://curated/tabular/market_ohlcv_daily/exchange=ASX/
Sample keys: ['tabular/market_ohlcv_daily/exchange=ASX/trade_date=2026-03-04/snapshot.parquet', 'tabular/market_ohlcv_daily/exchange=ASX/trade_date=2026-03-05/snapshot.parquet', 'tabular/market_ohlcv_daily/exchange=ASX/trade_date=2026-03-06/snapshot.parquet', 'tabular/market_ohlcv_daily/exchange=ASX/trade_date=2026-03-09/snapshot.parquet', 'tabular/market_ohlcv_daily/exchange=ASX/trade_date=2026-03-10/snapshot.parquet']

=== SHAPE ===
(90, 15)
```

Further output included:

- schema/dtype inspection,
- null-count summary showing no nulls across the 15 columns,
- sample rows from the curated OHLCV dataset.

## Final Assessment

Overall result:

- PASS

1. Core platform
- Reset: PASS
- Startup: PASS
- Service access/login: PASS with non-GUI fallbacks
- Heartbeat DAG flow: PASS
- Heartbeat notebook: PASS

2. ASX pipeline
- Config: PASS
- Daily DAG: PASS
- Raw/conformed/curated population: PASS
- Read notebook: PASS

3. GUI automation
- Not available, fallback used
- Browser/UI automation capability was not available in this Codex environment.
- Closest reliable fallback methods were used instead: `curl`, Jupyter API, Airflow CLI, Airflow HTTP form login, and credentialed MinIO S3 access.

## Failures and Observations

Confirmed defects:

- None confirmed during this execution.

External dependency issues:

- None observed during this execution.
- Yahoo Finance access succeeded for the ASX daily DAG run in this environment.

Environment/tooling limitations:

- GUI AUTOMATION NOT AVAILABLE in this Codex environment.
- Localhost HTTP checks and Docker daemon access were blocked inside the sandbox and required elevated execution against the host environment.

Stale documentation noticed during execution:

- `docker-compose.yaml` emits a Compose warning that the `version` attribute is obsolete and ignored.
- No additional stale documentation issues were identified during this validation run beyond that runtime warning.
