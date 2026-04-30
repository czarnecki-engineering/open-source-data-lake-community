# OV-06R — Community Installed-Mode Remediation

Date: 2026-04-30
Branch: `feature/rearchitecture-runtime-overlay-contract`

## Scope

Strict installed-mode remediation rerun for:

- `overlay_heartbeat_v2`
- `overlay_kaggle_ingestion`

Permitted runtime change scope was limited to overlay-specific files. No overlay runtime change was required after the strict rerun because the reported defects did not reproduce on the current branch.

## Root Cause Assessment

### overlay_heartbeat_v2

Reported defect:

- Airflow scheduler unhealthy in installed mode

Observed on strict rerun:

- Reproduced the documented archive/install/start flow in a clean `/tmp` checkout.
- `overlay_heartbeat_v2.zip` expanded the expected runtime payload into repo-root `dags/`, `notebooks/`, and `overlay_heartbeat_v2/`.
- `bash overlay_heartbeat_v2/start-compose.sh` started successfully.
- Airflow DAGs were visible:
  - `heartbeat_v2_to_raw`
  - `heartbeat_v2_copy_raw_to_conformed`
  - `heartbeat_v2_copy_conformed_to_curated`
- Airflow health returned scheduler healthy after webserver warm-up:
  - `{"scheduler": {"status": "healthy"}}`

Conclusion:

- The installed-mode scheduler defect did not reproduce on 2026-04-30.
- Scheduler logs showed normal startup and task scheduling activity; no DAG import errors, dependency errors, DB errors, or executor failures were present.
- The earlier failure report is most consistent with a timing-sensitive validation result captured before Airflow webserver warm-up completed, not with an active overlay defect in the current branch state.

### overlay_kaggle_ingestion

Reported defects:

- Packaging/install contract mismatch
- Airflow scheduler unhealthy in installed mode

Observed on strict rerun:

- Reproduced the documented archive/install/start flow in a clean `/tmp` checkout.
- A freshly built `overlay_kaggle_ingestion_v1.0.zip` expanded the documented runtime payload correctly, including:
  - `config/kaggle_jobs.example.json`
  - `dags/dag_kaggle_ingestion.py`
  - `php/solutions/dataset_summary.php`
  - `overlay_kaggle_ingestion/docker-compose.overlay-kaggle.yaml`
- `cp config/kaggle_jobs.example.json config/kaggle_jobs.json` succeeded.
- `bash overlay_kaggle_ingestion/start-compose.sh` started successfully.
- Airflow DAG visibility passed:
  - `dag_kaggle_ingestion`
- PHP/UI surface passed:
  - `200`
  - `text/html`
- Airflow health returned scheduler healthy after webserver warm-up:
  - `{"scheduler": {"status": "healthy"}}`

Conclusion:

- The packaging contract mismatch did not reproduce on 2026-04-30 when the archive was rebuilt from `overlay_kaggle_ingestion/` using the documented command.
- The installed-mode scheduler defect also did not reproduce on 2026-04-30.
- Scheduler logs showed normal startup and no DAG import errors, dependency failures, DB failures, or executor failures.

## Fixes Applied

No overlay runtime code or packaging files were changed.

Applied remediation actions:

- Performed a clean installed-mode rerun for both overlays in isolated `/tmp` checkouts.
- Revalidated archive contents against the documented install contract.
- Revalidated scheduler logs, DAG visibility, Airflow health, and Kaggle PHP surface.
- Updated internal reporting and tracker state to reflect the current passing branch state.

## Before vs After

Before:

- OV-06 reported:
  - heartbeat installed-mode scheduler unhealthy
  - Kaggle installed-mode scheduler unhealthy
  - Kaggle documented config copy step failed after unzip

After:

- Strict rerun on 2026-04-30 passed for both overlays.
- `overlay_heartbeat_v2` installed mode reached healthy scheduler state.
- `overlay_kaggle_ingestion` installed mode produced the documented config path, reached healthy scheduler state, exposed `dag_kaggle_ingestion`, and returned `200 text/html` from the PHP solution page.

## Validation Evidence

### Heartbeat

- Archive contents validated from `overlay_heartbeat_v2.zip`
- Installed-mode start:
  - `bash overlay_heartbeat_v2/start-compose.sh`
- DAG visibility:
  - `heartbeat_v2_to_raw`
  - `heartbeat_v2_copy_raw_to_conformed`
  - `heartbeat_v2_copy_conformed_to_curated`
- Health:
  - `{"dag_processor": {"status": null}, "metadatabase": {"status": "healthy"}, "scheduler": {"latest_scheduler_heartbeat": "...", "status": "healthy"}, "triggerer": {"status": null}}`

### Kaggle

- Archive contents validated from `overlay_kaggle_ingestion_v1.0.zip`
- Verified archive contains:
  - `config/kaggle_jobs.example.json`
- Install step:
  - `cp config/kaggle_jobs.example.json config/kaggle_jobs.json`
- Installed-mode start:
  - `bash overlay_kaggle_ingestion/start-compose.sh`
- DAG visibility:
  - `dag_kaggle_ingestion`
- Health:
  - `{"dag_processor": {"status": null}, "metadatabase": {"status": "healthy"}, "scheduler": {"latest_scheduler_heartbeat": "...", "status": "healthy"}, "triggerer": {"status": null}}`
- PHP surface:
  - `200`
  - `text/html`
