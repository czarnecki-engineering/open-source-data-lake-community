# OV-10C — Community Kaggle Installed-Mode Remediation

## Scope

- Repository: Community only
- Overlay: `overlay_kaggle_ingestion`
- Reference baseline: `/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-supported`
- Validation date: 2026-04-30

## Original Failure

Earlier installed-mode validation recorded two Kaggle issues in Community:

1. Documentation and archive mismatch
   - The documented installed step `cp config/kaggle_jobs.example.json config/kaggle_jobs.json` previously failed because the validation run reported that `config/kaggle_jobs.example.json` was missing after unzip.
2. Installed runtime behaviour
   - The same validation run recorded `scheduler.status` as `unhealthy` from `http://localhost:8080/health`.

## Reproduction And Comparison

### Community rerun

Clean target:

```bash
rm -rf /tmp/ov10c_kaggle
mkdir -p /tmp/ov10c_kaggle
```

Method:

- copied the Community repo into `/tmp/ov10c_kaggle`
- removed the Kaggle overlay payload from the temp checkout
- built the archive from `overlay_kaggle_ingestion/`
- unzipped it into the temp checkout
- ran `cp config/kaggle_jobs.example.json config/kaggle_jobs.json`
- started with `bash overlay_kaggle_ingestion/start-compose.sh`

Observed results:

- Archive contents were correct and included `config/`, `scripts/`, `dags/`, `notebooks/`, `php/`, and `overlay_kaggle_ingestion/`
- `config/kaggle_jobs.example.json` existed immediately after unzip
- `cp config/kaggle_jobs.example.json config/kaggle_jobs.json` succeeded
- `docker compose ... ps` showed `airflow-postgres`, `airflow-scheduler`, `airflow-webserver`, `jupyter`, `minio`, and `php` up
- `curl http://localhost:8080/health` returned scheduler `healthy` after normal warm-up
- `docker compose ... logs airflow-scheduler` showed normal scheduler startup and task execution

### Supported rerun

Clean target:

```bash
rm -rf /tmp/ov10c_supported_kaggle
mkdir -p /tmp/ov10c_supported_kaggle
```

Method matched the Community rerun using the Supported overlay as the reference baseline.

Observed results:

- Archive contents also included `config/`, `scripts/`, `dags/`, `notebooks/`, `php/`, and `overlay_kaggle_ingestion/`
- `config/kaggle_jobs.example.json` existed after unzip
- `cp config/kaggle_jobs.example.json config/kaggle_jobs.json` succeeded
- scheduler health became `healthy` after warm-up

## Root Cause Assessment

### A. Documentation / archive mismatch

Current-state diagnosis:

- Not reproducible from the current Community tree
- The current archive command produces a zip with `config/kaggle_jobs.example.json` at archive root
- The installed copy command succeeds without manual intervention in a fresh temp checkout

Most likely explanation:

- The historical OV-06 failure came from an earlier packaging or validation state that no longer matches the current tree
- The remaining gap in the current tree was documentation precision rather than archive contents

### B. Runtime behaviour issue

Current-state diagnosis:

- Not reproducible from the current Community tree
- Community and Supported both reached healthy scheduler state after the same warm-up pattern
- No Community-only runtime divergence was required to make installed mode healthy

Most likely explanation:

- The earlier unhealthy scheduler observation was transient startup timing rather than a persistent Kaggle overlay defect in the current tree

## Fixes Applied

Documentation-only remediation was applied in Community:

- `overlay_kaggle_ingestion/README.md`
- `overlay_kaggle_ingestion/RUNBOOK.md`
- `overlay_kaggle_ingestion/overlay_kaggle_ingestion/README.md`
- `overlay_kaggle_ingestion/overlay_kaggle_ingestion/RUNBOOK.md`

Changes made:

- made the archive command explicit and self-contained with `cd ..` after zip
- stated the authoritative archive root contents
- stated that `config/kaggle_jobs.example.json` must exist immediately after unzip
- documented the validated health checks for installed mode

No runtime files were modified because the current installed runtime already matches Supported behaviour for this overlay.

## Before Vs After

Before:

- OV-06 recorded a failing `cp` step
- OV-06 recorded scheduler health as unhealthy
- Kaggle installed-mode docs did not explicitly state the validated archive-root expectation or the scheduler-health verification step

After:

- `cp config/kaggle_jobs.example.json config/kaggle_jobs.json` succeeds in a fresh temp checkout
- scheduler health reaches `healthy` in Community and Supported
- Community installed-mode docs now describe the validated archive layout and runtime checks directly

## Validation Evidence

Community evidence:

- `unzip -l /tmp/ov10c_kaggle/community_overlay_kaggle_ingestion_v1.0.zip` listed `config/kaggle_jobs.example.json`
- `cp /tmp/ov10c_kaggle/config/kaggle_jobs.example.json /tmp/ov10c_kaggle/config/kaggle_jobs.json` succeeded
- `docker compose -f docker-compose.yaml -f overlay_kaggle_ingestion/docker-compose.overlay-kaggle.yaml ps` showed all required services up
- `curl -sS http://localhost:8080/health` returned scheduler `healthy`
- `docker compose ... exec -T airflow-webserver airflow dags list | rg 'dag_kaggle_ingestion'` showed the DAG
- `curl -sS -o /dev/null -w '%{http_code}\n' http://localhost:8088/solutions/dataset_summary.php` returned `200`
- `curl -sS -I http://localhost:8888` returned `405`, confirming Jupyter was reachable
- `docker compose ... logs minio-init` showed `raw`, `conformed`, and `curated` bucket creation

Supported evidence:

- `unzip -l /tmp/ov10c_supported_kaggle/supported_overlay_kaggle_ingestion_v1.0.zip` listed `config/kaggle_jobs.example.json`
- `cp /tmp/ov10c_supported_kaggle/config/kaggle_jobs.example.json /tmp/ov10c_supported_kaggle/config/kaggle_jobs.json` succeeded
- `curl -sS http://localhost:8080/health` returned scheduler `healthy`
- `docker compose ... exec -T airflow-webserver airflow dags list | rg 'dag_kaggle_ingestion'` showed the DAG

## Outcome

- Documentation / packaging gap: addressed with explicit installed-mode documentation
- Runtime issue: validated as already resolved in the current Community tree; no runtime code change required
- Final installed-mode result: pass
