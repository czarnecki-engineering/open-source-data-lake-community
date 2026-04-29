# Task 14 — Remediation Plan

## 1. Summary

- Task 13 overall result: FAIL
- Number of critical issues: 2
- Number of non-critical issues: 3
- Remediation strategy: Remove the single startup-path env gap that allowed blank critical variables, correct the base runtime credential dependency chain affected by that gap, remove overlay credential fallbacks that violate the env model, and align Community documentation to the already-implemented split-service PostgreSQL runtime and overlay activation path.

## 2. Root Cause Analysis

### 2.1 Env / Secrets Model
- Root cause: The documented Community startup path only verified that `.env` existed and did not enforce completeness for the required runtime variable set, while some overlay compose files still retained MinIO credential fallbacks instead of relying exclusively on env injection.
- Impact: Critical runtime values could resolve blank at startup, base services could diverge in effective credentials, and overlays remained partially non-compliant with the contract requirement that runtimes inject secrets.

### 2.2 Runtime Startup Failure
- Root cause: Community startup accepted an incomplete env file and proceeded into `docker compose up`, allowing the stack to build and partially start with blank ports and credentials.
- Impact: The isolated startup never reached a stable healthy detached state, random host ports were assigned, and Stage 4 validation failed at the runtime entry point.

### 2.3 MinIO Init Failure
- Root cause: The MinIO bootstrap path did not receive a complete credential set consistent with the MinIO service that actually started, producing an access-denied failure in `minio-init`.
- Impact: Required `raw`, `conformed`, and `curated` bucket provisioning did not complete, so the object-store portion of the contract was left incomplete even though `minio` itself became healthy.

### 2.4 Airflow Postgres Failure
- Root cause: `airflow-postgres` started without the required PostgreSQL superuser/database variables because blank env-derived values were permitted through the documented startup path.
- Impact: PostgreSQL restarted continuously, `airflow-user-init` never ran, and both Airflow runtime services remained unstarted.

### 2.5 Logical Airflow Documentation Drift
- Root cause: Repository documentation still describes a legacy single-container SQLite Airflow model and `airflow-db` persistence even though the implemented runtime and overlay guard now require `airflow-webserver`, `airflow-scheduler`, and PostgreSQL.
- Impact: The negative logical-airflow validation failed at the documentation level despite the compose/runtime implementation already being aligned.

### 2.6 Overlay Credential Fallbacks
- Root cause: Kaggle and ASX overlay Jupyter definitions still embed `${MINIO_ROOT_USER:-minioadmin}` and `${MINIO_ROOT_PASSWORD:-minioadmin}` fallbacks.
- Impact: Overlay runtime files still imply active default credentials, weakening env/secrets enforcement and conflicting with the contract expectation that runtime credentials come from injected env values.

## 3. Remediation Groups

### Group 1 — Enforce required Community env completeness before startup
- Problem: Task 13 showed that `./start-compose.sh` accepted an incomplete `.env`, emitted missing-variable warnings, and continued into a failed startup with blank critical values.
- Scope: Community base startup validation only; no overlay semantics changes beyond enforcing the already-required env inventory.
- Files impacted:
  - `start-compose.sh`
  - `.env.example`
- Change type: Validation logic and operator-facing env inventory clarification.
- Constraints:
  - Must not change the overlay contract.
  - Must not add new runtime behaviour beyond failing early when required Community vars are missing or blank.
  - Must remain Community-only.
- Expected outcome: `./start-compose.sh` rejects incomplete env input before compose startup, preventing blank credentials and blank port mappings from reaching the runtime.

### Group 2 — Correct base runtime credential dependency wiring
- Problem: Task 13 recorded two direct runtime failures from the accepted blank env state: `airflow-postgres` restarted because required PostgreSQL values were missing, and `minio-init` exited with access denied because bootstrap credentials were not aligned with the running MinIO service.
- Scope: Community base runtime dependency path only, limited to the already-defined services `airflow-postgres`, `minio`, and `minio-init`.
- Files impacted:
  - `docker-compose.yaml`
  - `start-compose.sh`
  - `.env.example`
- Change type: Runtime configuration dependency correction and startup-path validation alignment.
- Constraints:
  - Must not introduce new services, new credentials, or alternative storage/database designs.
  - Must preserve the existing split-service Airflow and MinIO contract.
  - Must not broaden scope into Supported runtime or overlay redesign.
- Expected outcome: With a complete env file, `airflow-postgres` initializes successfully, `minio-init` provisions the standard buckets successfully, and downstream Airflow services are no longer blocked by base dependency startup failure.

### Group 3 — Remove overlay credential fallbacks from Community overlays
- Problem: Task 13 identified hardcoded MinIO credential fallbacks in Community overlay Jupyter definitions, which kept the env/secrets model from passing even after base runtime placeholders were centralized.
- Scope: Community overlay compose files only for the affected Kaggle and ASX overlays in both dev and packaged forms.
- Files impacted:
  - `overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml`
  - `overlay_kaggle_ingestion/overlay_kaggle_ingestion/docker-compose.overlay-kaggle.yaml`
  - `overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml`
  - `overlay_asx_historic_csv/overlay_asx_historic_csv/docker-compose.overlay-asx-historic-csv.yaml`
- Change type: Overlay env compliance cleanup.
- Constraints:
  - Must not change overlay composition structure or service targeting.
  - Must not introduce new overlay variables.
  - Must preserve existing overlay behaviour when the required env is present.
- Expected outcome: Community overlays rely exclusively on injected MinIO credentials and no longer embed active default fallbacks.

### Group 4 — Align Community documentation to the implemented runtime and wrapper contract
- Problem: Task 13 recorded documentation that still describes single-container SQLite Airflow, `airflow-db` persistence, incomplete overlay usage, and out-of-scope cleanup guidance.
- Scope: Community operator documentation only.
- Files impacted:
  - `README.md`
  - `RUNBOOK.md`
- Change type: Documentation alignment.
- Constraints:
  - Must reflect the current implemented Community runtime only.
  - Must not describe new workflows beyond the existing `./start-compose.sh`, `./stop-compose.sh`, and `--overlay` wrapper contract.
  - Must not change architecture or add new operational modes.
- Expected outcome: Documentation matches the split-service PostgreSQL runtime, documents overlay activation through the root wrapper, removes stale `airflow-db`/SQLite references, and stays within the scoped operating model used by validation.

## 4. Execution Plan

1. Group 1 — Enforce required Community env completeness before startup.
   Justification: This is the earliest control point and addresses the primary root cause that allowed blank credentials and blank ports to propagate into runtime startup.
2. Group 2 — Correct base runtime credential dependency wiring.
   Justification: After startup gating is explicit, the base runtime dependency chain can be corrected and validated against the same required env model without ambiguity.
3. Group 3 — Remove overlay credential fallbacks from Community overlays.
   Justification: Overlay cleanup should happen after the base env model is fixed so overlays can align to the final enforced variable contract rather than to a transitional state.
4. Group 4 — Align Community documentation to the implemented runtime and wrapper contract.
   Justification: Documentation should be updated last so it reflects the final remediated Community behaviour and does not document partial intermediate states.
5. Task 19 validation rerun.
   Justification: Re-validation should only happen after startup enforcement, base dependency correction, overlay compliance, and documentation alignment are all complete.

## 5. Validation Strategy

### Group 1 Validation
- Success criteria:
  - `./start-compose.sh` fails before compose startup when any required Community env variable is missing or blank.
  - The failure message identifies the incomplete env condition clearly enough for operator correction.
  - A complete `.env` is accepted without missing-variable warnings for the required inventory.
- Failure indicators:
  - Compose still starts with blank critical values.
  - Random host ports are still assigned because required port variables were blank.
  - Missing env input is only detected after containers are created.

### Group 2 Validation
- Success criteria:
  - `airflow-postgres` initializes successfully with the required env values present.
  - `minio-init` completes successfully and provisions `raw`, `conformed`, and `curated`.
  - `airflow-user-init`, `airflow-webserver`, and `airflow-scheduler` are no longer blocked by failed base dependencies.
- Failure indicators:
  - `airflow-postgres` restarts with missing-password or missing-database errors.
  - `minio-init` still exits non-zero with access denied or equivalent bootstrap credential errors.
  - Airflow services remain `Created` because upstream dependencies never become healthy.

### Group 3 Validation
- Success criteria:
  - The four affected overlay compose files no longer contain `minioadmin` credential fallbacks.
  - Overlay Jupyter env wiring resolves MinIO credentials from injected env values only.
- Failure indicators:
  - Any affected overlay file still contains `${MINIO_ROOT_USER:-...}` or `${MINIO_ROOT_PASSWORD:-...}`.
  - Overlay runtime files still imply active default credentials independent of `.env`.

### Group 4 Validation
- Success criteria:
  - `README.md` and `RUNBOOK.md` describe Airflow as split-service with PostgreSQL-backed metadata.
  - Stale `airflow-db` and SQLite operational references are removed or replaced with the current model.
  - The root wrapper `--overlay` activation path is documented consistently with `start-compose.sh`.
  - Broad cleanup guidance outside the scoped validation model is removed from Community operational docs.
- Failure indicators:
  - Documentation still refers to a single logical `airflow` container.
  - Documentation still describes SQLite metadata or the `airflow-db` volume as the active model.
  - Overlay activation remains undocumented or contradicts the wrapper behaviour.

## 6. Proposed Next Tasks

- Task 15 — Enforce Community env completeness in `start-compose.sh`
- Task 16 — Correct Community base runtime credential dependency wiring
- Task 17 — Remove Community overlay MinIO credential fallbacks
- Task 18 — Align Community documentation with split-service PostgreSQL runtime and wrapper overlay activation
- Task 19 — Re-run Community Stage 4 validation

## 7. Constraints Confirmation

- No contract changes required: YES
- Changes limited to Community repo: YES
- Overlay model preserved: YES
- No new architecture introduced: YES
