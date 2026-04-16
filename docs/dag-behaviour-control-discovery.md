# DAG Behaviour Control Discovery

## 1. DAG inventory

| file | dag_id | classification |
| --- | --- | --- |
| `dags/heartbeat_1m_to_raw.py` | `heartbeat_1m_to_raw` | heartbeat DAG |
| `dags/heartbeat_1m_copy_raw_to_conformed.py` | `heartbeat_1m_copy_raw_to_conformed` | heartbeat DAG |
| `dags/heartbeat_1m_copy_conformed_to_curated.py` | `heartbeat_1m_copy_conformed_to_curated` | heartbeat DAG |
| `dags/asx200_ohlcv_daily_to_raw.py` | `asx200_ohlcv_daily_to_raw` | non-heartbeat DAG |
| `dags/asx200_ohlcv_raw_to_conformed_parquet.py` | `asx200_ohlcv_raw_to_conformed_parquet` | non-heartbeat DAG |
| `dags/asx200_ohlcv_conformed_to_curated_snapshot_v2.py` | `asx200_ohlcv_conformed_to_curated_snapshot_v2` | non-heartbeat DAG |
| `dags/asx200_ohlcv_backfill_to_raw.py` | `asx200_ohlcv_backfill_to_raw` | non-heartbeat DAG |

Instantiation pattern for every DAG:

- All seven DAGs are instantiated with a `with DAG(...) as dag:` context-manager pattern.
- Evidence:
  - `dags/heartbeat_1m_to_raw.py:26` `with DAG(`
  - `dags/heartbeat_1m_copy_raw_to_conformed.py:43` `with DAG(`
  - `dags/heartbeat_1m_copy_conformed_to_curated.py:38` `with DAG(`
  - `dags/asx200_ohlcv_daily_to_raw.py:174` `with DAG(`
  - `dags/asx200_ohlcv_raw_to_conformed_parquet.py:131` `with DAG(`
  - `dags/asx200_ohlcv_conformed_to_curated_snapshot_v2.py:173` `with DAG(`
  - `dags/asx200_ohlcv_backfill_to_raw.py:338` `with DAG(`

Classification evidence:

- `heartbeat_1m_to_raw` writes to a heartbeat path:
  - `dags/heartbeat_1m_to_raw.py:22` `key = f"heartbeat/airflow_time_{now.strftime('%Y%m%d_%H%M%S')}.txt"`
- `heartbeat_1m_copy_raw_to_conformed` operates only on `heartbeat/`:
  - `dags/heartbeat_1m_copy_raw_to_conformed.py:12` `PREFIX = "heartbeat/"`
- `heartbeat_1m_copy_conformed_to_curated` operates only on `heartbeat/`:
  - `dags/heartbeat_1m_copy_conformed_to_curated.py:12` `PREFIX = "heartbeat/"`
- The remaining four DAG ids are ASX OHLCV DAGs, not heartbeat DAGs:
  - `dags/asx200_ohlcv_daily_to_raw.py:175` `dag_id="asx200_ohlcv_daily_to_raw",`
  - `dags/asx200_ohlcv_raw_to_conformed_parquet.py:132` `dag_id="asx200_ohlcv_raw_to_conformed_parquet",`
  - `dags/asx200_ohlcv_conformed_to_curated_snapshot_v2.py:174` `dag_id="asx200_ohlcv_conformed_to_curated_snapshot_v2",`
  - `dags/asx200_ohlcv_backfill_to_raw.py:339` `dag_id="asx200_ohlcv_backfill_to_raw",`

## 2. Current scheduling configuration

### `heartbeat_1m_to_raw` in `dags/heartbeat_1m_to_raw.py`

- `dag_id`
  - Evidence: `dags/heartbeat_1m_to_raw.py:27` `dag_id="heartbeat_1m_to_raw",`
- `start_date`
  - Evidence: `dags/heartbeat_1m_to_raw.py:28` `start_date=pendulum.datetime(2024, 1, 1, tz="Australia/Melbourne"),`
- `schedule`
  - Evidence: `dags/heartbeat_1m_to_raw.py:29` `schedule="* * * * *",`
- `schedule_interval`
  - NOT VERIFIED FROM SOURCE
- `catchup`
  - Evidence: `dags/heartbeat_1m_to_raw.py:30` `catchup=False,`
- `max_active_runs`
  - Evidence: `dags/heartbeat_1m_to_raw.py:31` `max_active_runs=1,`
- `is_paused_upon_creation`
  - NOT VERIFIED FROM SOURCE
- Other scheduling-related settings actually defined
  - Evidence: `dags/heartbeat_1m_to_raw.py:32` `tags=["raw", "minio"],`

### `heartbeat_1m_copy_raw_to_conformed` in `dags/heartbeat_1m_copy_raw_to_conformed.py`

- `dag_id`
  - Evidence: `dags/heartbeat_1m_copy_raw_to_conformed.py:44` `dag_id="heartbeat_1m_copy_raw_to_conformed",`
- `start_date`
  - Evidence: `dags/heartbeat_1m_copy_raw_to_conformed.py:45` `start_date=datetime(2024, 1, 1),`
- `schedule`
  - NOT VERIFIED FROM SOURCE
- `schedule_interval`
  - Evidence: `dags/heartbeat_1m_copy_raw_to_conformed.py:46` `schedule_interval="*/1 * * * *",  # every minute`
- `catchup`
  - Evidence: `dags/heartbeat_1m_copy_raw_to_conformed.py:47` `catchup=False,`
- `max_active_runs`
  - NOT VERIFIED FROM SOURCE
- `is_paused_upon_creation`
  - NOT VERIFIED FROM SOURCE
- Other scheduling-related settings actually defined
  - Evidence: `dags/heartbeat_1m_copy_raw_to_conformed.py:38-41` `default_args = { "owner": "airflow", "retries": 0, }`
  - Evidence: `dags/heartbeat_1m_copy_raw_to_conformed.py:48` `default_args=default_args,`
  - Evidence: `dags/heartbeat_1m_copy_raw_to_conformed.py:49` `tags=["minio", "raw", "conformed"],`

### `heartbeat_1m_copy_conformed_to_curated` in `dags/heartbeat_1m_copy_conformed_to_curated.py`

- `dag_id`
  - Evidence: `dags/heartbeat_1m_copy_conformed_to_curated.py:39` `dag_id="heartbeat_1m_copy_conformed_to_curated",`
- `start_date`
  - Evidence: `dags/heartbeat_1m_copy_conformed_to_curated.py:40` `start_date=datetime(2024, 1, 1),`
- `schedule`
  - NOT VERIFIED FROM SOURCE
- `schedule_interval`
  - Evidence: `dags/heartbeat_1m_copy_conformed_to_curated.py:41` `schedule_interval="*/1 * * * *",  # every minute`
- `catchup`
  - Evidence: `dags/heartbeat_1m_copy_conformed_to_curated.py:42` `catchup=False,`
- `max_active_runs`
  - NOT VERIFIED FROM SOURCE
- `is_paused_upon_creation`
  - NOT VERIFIED FROM SOURCE
- Other scheduling-related settings actually defined
  - Evidence: `dags/heartbeat_1m_copy_conformed_to_curated.py:43` `tags=["minio", "conformed", "curated"],`

### `asx200_ohlcv_daily_to_raw` in `dags/asx200_ohlcv_daily_to_raw.py`

- `dag_id`
  - Evidence: `dags/asx200_ohlcv_daily_to_raw.py:175` `dag_id="asx200_ohlcv_daily_to_raw",`
- `start_date`
  - Evidence: `dags/asx200_ohlcv_daily_to_raw.py:176` `start_date=pendulum.datetime(2024, 1, 1, tz="Australia/Melbourne"),`
- `schedule`
  - Evidence: `dags/asx200_ohlcv_daily_to_raw.py:177` `schedule="*/5 * * * *",  # adjust as desired; 5-min is safer than 1-min for Yahoo`
- `schedule_interval`
  - NOT VERIFIED FROM SOURCE
- `catchup`
  - Evidence: `dags/asx200_ohlcv_daily_to_raw.py:178` `catchup=False,`
- `max_active_runs`
  - Evidence: `dags/asx200_ohlcv_daily_to_raw.py:179` `max_active_runs=1,`
- `is_paused_upon_creation`
  - NOT VERIFIED FROM SOURCE
- Other scheduling-related settings actually defined
  - Evidence: `dags/asx200_ohlcv_daily_to_raw.py:180` `tags=["minio", "raw", "ohlcv", "asx"],`

### `asx200_ohlcv_raw_to_conformed_parquet` in `dags/asx200_ohlcv_raw_to_conformed_parquet.py`

- `dag_id`
  - Evidence: `dags/asx200_ohlcv_raw_to_conformed_parquet.py:132` `dag_id="asx200_ohlcv_raw_to_conformed_parquet",`
- `start_date`
  - Evidence: `dags/asx200_ohlcv_raw_to_conformed_parquet.py:133` `start_date=pendulum.datetime(2024, 1, 1, tz="Australia/Melbourne"),`
- `schedule`
  - Evidence: `dags/asx200_ohlcv_raw_to_conformed_parquet.py:134` `schedule="*/5 * * * *",`
- `schedule_interval`
  - NOT VERIFIED FROM SOURCE
- `catchup`
  - Evidence: `dags/asx200_ohlcv_raw_to_conformed_parquet.py:135` `catchup=False,`
- `max_active_runs`
  - Evidence: `dags/asx200_ohlcv_raw_to_conformed_parquet.py:136` `max_active_runs=1,`
- `is_paused_upon_creation`
  - NOT VERIFIED FROM SOURCE
- Other scheduling-related settings actually defined
  - Evidence: `dags/asx200_ohlcv_raw_to_conformed_parquet.py:137` `tags=["minio", "raw", "conformed", "ohlcv"],`

### `asx200_ohlcv_conformed_to_curated_snapshot_v2` in `dags/asx200_ohlcv_conformed_to_curated_snapshot_v2.py`

- `dag_id`
  - Evidence: `dags/asx200_ohlcv_conformed_to_curated_snapshot_v2.py:174` `dag_id="asx200_ohlcv_conformed_to_curated_snapshot_v2",`
- `start_date`
  - Evidence: `dags/asx200_ohlcv_conformed_to_curated_snapshot_v2.py:175` `start_date=pendulum.datetime(2024, 1, 1, tz="Australia/Melbourne"),`
- `schedule`
  - Evidence: `dags/asx200_ohlcv_conformed_to_curated_snapshot_v2.py:176` `schedule="*/10 * * * *",`
- `schedule_interval`
  - NOT VERIFIED FROM SOURCE
- `catchup`
  - Evidence: `dags/asx200_ohlcv_conformed_to_curated_snapshot_v2.py:177` `catchup=False,`
- `max_active_runs`
  - Evidence: `dags/asx200_ohlcv_conformed_to_curated_snapshot_v2.py:178` `max_active_runs=1,`
- `is_paused_upon_creation`
  - NOT VERIFIED FROM SOURCE
- Other scheduling-related settings actually defined
  - Evidence: `dags/asx200_ohlcv_conformed_to_curated_snapshot_v2.py:179` `tags=["minio", "conformed", "curated", "ohlcv", "snapshot"],`

### `asx200_ohlcv_backfill_to_raw` in `dags/asx200_ohlcv_backfill_to_raw.py`

- `dag_id`
  - Evidence: `dags/asx200_ohlcv_backfill_to_raw.py:339` `dag_id="asx200_ohlcv_backfill_to_raw",`
- `start_date`
  - Evidence: `dags/asx200_ohlcv_backfill_to_raw.py:340` `start_date=pendulum.datetime(2024, 1, 1, tz="Australia/Melbourne"),`
- `schedule`
  - Evidence: `dags/asx200_ohlcv_backfill_to_raw.py:341` `schedule="@daily",  # temporarily scheduled; disable once complete`
- `schedule_interval`
  - NOT VERIFIED FROM SOURCE
- `catchup`
  - Evidence: `dags/asx200_ohlcv_backfill_to_raw.py:342` `catchup=False,`
- `max_active_runs`
  - Evidence: `dags/asx200_ohlcv_backfill_to_raw.py:343` `max_active_runs=1,`
- `is_paused_upon_creation`
  - NOT VERIFIED FROM SOURCE
- Other scheduling-related settings actually defined
  - Evidence: `dags/asx200_ohlcv_backfill_to_raw.py:344` `tags=["minio", "raw", "ohlcv", "asx", "backfill", "yfinance"],`

Repo-level Airflow settings relevant to scheduling behavior:

- Airflow version
  - Evidence: `docker/airflow/Dockerfile:1` `FROM apache/airflow:2.10.3`
- DAGs are not paused by default on creation
  - Evidence: `docker-compose.yaml:58` `AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: "False"`

## 3. Desired behaviour classification

Rule being evaluated:

- heartbeat DAGs -> `KEEP_AUTOMATIC`
- all other DAGs -> `CHANGE_TO_MANUAL`

### 3.1 KEEP_AUTOMATIC

- `heartbeat_1m_to_raw`
  - Evidence:
    - `dags/heartbeat_1m_to_raw.py:27` `dag_id="heartbeat_1m_to_raw",`
    - `dags/heartbeat_1m_to_raw.py:22` `key = f"heartbeat/airflow_time_{now.strftime('%Y%m%d_%H%M%S')}.txt"`
- `heartbeat_1m_copy_raw_to_conformed`
  - Evidence:
    - `dags/heartbeat_1m_copy_raw_to_conformed.py:44` `dag_id="heartbeat_1m_copy_raw_to_conformed",`
    - `dags/heartbeat_1m_copy_raw_to_conformed.py:12` `PREFIX = "heartbeat/"`
- `heartbeat_1m_copy_conformed_to_curated`
  - Evidence:
    - `dags/heartbeat_1m_copy_conformed_to_curated.py:39` `dag_id="heartbeat_1m_copy_conformed_to_curated",`
    - `dags/heartbeat_1m_copy_conformed_to_curated.py:12` `PREFIX = "heartbeat/"`

### 3.2 CHANGE_TO_MANUAL

- `asx200_ohlcv_daily_to_raw`
  - Evidence:
    - `dags/asx200_ohlcv_daily_to_raw.py:175` `dag_id="asx200_ohlcv_daily_to_raw",`
    - `dags/asx200_ohlcv_daily_to_raw.py:177` `schedule="*/5 * * * *",  # adjust as desired; 5-min is safer than 1-min for Yahoo`
- `asx200_ohlcv_raw_to_conformed_parquet`
  - Evidence:
    - `dags/asx200_ohlcv_raw_to_conformed_parquet.py:132` `dag_id="asx200_ohlcv_raw_to_conformed_parquet",`
    - `dags/asx200_ohlcv_raw_to_conformed_parquet.py:134` `schedule="*/5 * * * *",`
- `asx200_ohlcv_conformed_to_curated_snapshot_v2`
  - Evidence:
    - `dags/asx200_ohlcv_conformed_to_curated_snapshot_v2.py:174` `dag_id="asx200_ohlcv_conformed_to_curated_snapshot_v2",`
    - `dags/asx200_ohlcv_conformed_to_curated_snapshot_v2.py:176` `schedule="*/10 * * * *",`
- `asx200_ohlcv_backfill_to_raw`
  - Evidence:
    - `dags/asx200_ohlcv_backfill_to_raw.py:339` `dag_id="asx200_ohlcv_backfill_to_raw",`
    - `dags/asx200_ohlcv_backfill_to_raw.py:341` `schedule="@daily",  # temporarily scheduled; disable once complete`

### 3.3 NOT_CLEAR_FROM_SOURCE

- None found.

## 4. Recommended implementation pattern

Recommended manual-trigger pattern for non-heartbeat DAGs:

- Set `schedule=None`.
- Keep `catchup=False`.
- Leave existing `start_date` unchanged.
- Leave existing `max_active_runs` unchanged where already defined.
- Do not rely on `is_paused_upon_creation` as the primary control.

Why this is the safest consistent pattern in this repo:

- Airflow 2.10.3 is the declared runtime.
  - Evidence: `docker/airflow/Dockerfile:1` `FROM apache/airflow:2.10.3`
- The repo already uses `schedule=` on four DAGs, including all four non-heartbeat DAGs that should become manual-only.
  - Evidence:
    - `dags/asx200_ohlcv_daily_to_raw.py:177` `schedule="*/5 * * * *",`
    - `dags/asx200_ohlcv_raw_to_conformed_parquet.py:134` `schedule="*/5 * * * *",`
    - `dags/asx200_ohlcv_conformed_to_curated_snapshot_v2.py:176` `schedule="*/10 * * * *",`
    - `dags/asx200_ohlcv_backfill_to_raw.py:341` `schedule="@daily",`
- Repo-level default DAG creation is unpaused, so `is_paused_upon_creation` would not by itself express "manual-trigger only" as directly as removing the schedule.
  - Evidence: `docker-compose.yaml:58` `AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: "False"`

Recommended exact DAG-level edit shape for non-heartbeat DAGs:

```python
with DAG(
    ...,
    schedule=None,
    catchup=False,
    ...
) as dag:
```

Heartbeat DAG recommendation:

- Keep heartbeat DAGs automatic.
- No scheduling cleanup is required to preserve current automatic behavior.
- Optional consistency cleanup only:
  - change the two heartbeat copy DAGs from `schedule_interval="*/1 * * * *"` to `schedule="*/1 * * * *"` so all DAGs use one scheduling argument style.
- This cleanup is optional because current source already mixes both styles under Airflow 2.10.3.
  - Evidence:
    - `dags/heartbeat_1m_to_raw.py:29` `schedule="* * * * *",`
    - `dags/heartbeat_1m_copy_raw_to_conformed.py:46` `schedule_interval="*/1 * * * *",`
    - `dags/heartbeat_1m_copy_conformed_to_curated.py:41` `schedule_interval="*/1 * * * *",`

Exact DAGs that would need schedule edits under the requested rule:

- `dags/asx200_ohlcv_daily_to_raw.py`
- `dags/asx200_ohlcv_raw_to_conformed_parquet.py`
- `dags/asx200_ohlcv_conformed_to_curated_snapshot_v2.py`
- `dags/asx200_ohlcv_backfill_to_raw.py`

## 5. Documentation follow-up needed

`README.md` should be updated after the DAG changes.

- Current source says the platform is healthy if `heartbeat DAGs are running`.
  - Evidence: `README.md:88-91`
- Current source does not document that non-heartbeat DAGs are manual-trigger only.
  - NOT VERIFIED FROM SOURCE

`RUNBOOK.md` should be updated after the DAG changes.

- Current source says the platform is healthy if `heartbeat DAGs are running`.
  - Evidence: `RUNBOOK.md:321-324`
- Current source does not document that non-heartbeat DAGs are manual-trigger only.
  - NOT VERIFIED FROM SOURCE

Minimum follow-up doc content implied by the requested rule:

- heartbeat DAGs run automatically
- all non-heartbeat DAGs require manual trigger from Airflow
- expected trigger order for manual ASX pipeline runs

## 6. Risks and edge cases

### 6.1 Implicit chaining is currently implemented by storage polling, not Airflow dependencies

Risk:

- If non-heartbeat DAGs are changed to manual-only, the raw -> conformed -> curated chain will no longer advance automatically.
- Operators will need to trigger downstream DAGs manually after upstream DAGs have produced data.

Evidence:

- `asx200_ohlcv_daily_to_raw` writes CSV objects into `raw/`.
  - `dags/asx200_ohlcv_daily_to_raw.py:102-105` `- write one CSV object per (ticker, trade_date) into raw/`
  - `dags/asx200_ohlcv_daily_to_raw.py:165-169` `s3.put_object(Bucket=RAW_BUCKET, Key=key, ...)`
- `asx200_ohlcv_raw_to_conformed_parquet` polls the raw bucket and converts unseen CSVs.
  - `dags/asx200_ohlcv_raw_to_conformed_parquet.py:87-92` `raw_keys = [...]` and `conformed_keys = set(...)`
  - `dags/asx200_ohlcv_raw_to_conformed_parquet.py:97-100` `if out_key in conformed_keys: continue  # append-only: do not overwrite`
- `asx200_ohlcv_conformed_to_curated_snapshot_v2` polls the conformed bucket and rebuilds snapshots when conformed data is newer.
  - `dags/asx200_ohlcv_conformed_to_curated_snapshot_v2.py:103-107` `conformed_objs = [...]`
  - `dags/asx200_ohlcv_conformed_to_curated_snapshot_v2.py:119-121` `if snapshot_last_modified and snapshot_last_modified >= latest_conformed: continue`

### 6.2 Heartbeat chain also depends on scheduled polling across three DAGs

Risk:

- The three heartbeat DAGs form an automatic chain only because each downstream DAG polls the `heartbeat/` prefix on a schedule.
- If any heartbeat DAG is accidentally changed to manual-only, the heartbeat health signal described in docs will stop propagating end to end.

Evidence:

- `heartbeat_1m_to_raw` writes `heartbeat/...` to the raw bucket.
  - `dags/heartbeat_1m_to_raw.py:22-23`
- `heartbeat_1m_copy_raw_to_conformed` lists raw and conformed objects under `PREFIX = "heartbeat/"`.
  - `dags/heartbeat_1m_copy_raw_to_conformed.py:12`
  - `dags/heartbeat_1m_copy_raw_to_conformed.py:23-24`
- `heartbeat_1m_copy_conformed_to_curated` lists conformed and curated objects under `PREFIX = "heartbeat/"`.
  - `dags/heartbeat_1m_copy_conformed_to_curated.py:12`
  - `dags/heartbeat_1m_copy_conformed_to_curated.py:23-24`

### 6.3 Backfill DAG already carries source evidence that it should stop being scheduled

Risk:

- The backfill DAG has explicit source commentary that its current daily schedule is temporary.
- Changing it to manual-only aligns with this comment, but operators may still rely on repeated scheduled retries while the backfill is in progress.

Evidence:

- `dags/asx200_ohlcv_backfill_to_raw.py:341` `schedule="@daily",  # temporarily scheduled; disable once complete`
- `dags/asx200_ohlcv_backfill_to_raw.py:190-191` `- uses a state file in raw/ to resume (skip completed tickers)` and `- records per-ticker failures to audit/errors.json`

### 6.4 Mixed scheduling argument syntax exists in source

Risk:

- The repo currently mixes `schedule=` and `schedule_interval=`.
- This is not a proven runtime problem from source, but it is an implementation-consistency concern when applying the manual-only rule.

Evidence:

- `schedule=` is used in five DAGs.
  - `dags/heartbeat_1m_to_raw.py:29`
  - `dags/asx200_ohlcv_daily_to_raw.py:177`
  - `dags/asx200_ohlcv_raw_to_conformed_parquet.py:134`
  - `dags/asx200_ohlcv_conformed_to_curated_snapshot_v2.py:176`
  - `dags/asx200_ohlcv_backfill_to_raw.py:341`
- `schedule_interval=` is used in two DAGs.
  - `dags/heartbeat_1m_copy_raw_to_conformed.py:46`
  - `dags/heartbeat_1m_copy_conformed_to_curated.py:41`

### 6.5 `is_paused_upon_creation` is not defined on any DAG

Risk:

- If the implementation plan depends on `is_paused_upon_creation`, that would be a new pattern in this repo.
- Source does not prove any current per-DAG usage of that setting.

Evidence:

- `rg -n "is_paused_upon_creation" dags` returned no matches.
- Repo-level default is unpaused:
  - `docker-compose.yaml:58` `AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: "False"`

## 7. Appendix: files inspected

- `dags/asx200_ohlcv_backfill_to_raw.py`
- `dags/asx200_ohlcv_conformed_to_curated_snapshot_v2.py`
- `dags/asx200_ohlcv_daily_to_raw.py`
- `dags/asx200_ohlcv_raw_to_conformed_parquet.py`
- `dags/heartbeat_1m_copy_conformed_to_curated.py`
- `dags/heartbeat_1m_copy_raw_to_conformed.py`
- `dags/heartbeat_1m_to_raw.py`
- `dags/README.md`
- `README.md`
- `RUNBOOK.md`
- `docker/airflow/Dockerfile`
- `docker-compose.yaml`

Local shared DAG helper modules inspected:

- No DAG in `dags/` imports a local shared helper module.
- Evidence: imports in inspected DAGs reference standard library modules, third-party packages, and Airflow modules only.
