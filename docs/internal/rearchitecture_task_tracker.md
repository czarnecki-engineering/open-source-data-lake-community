# Rearchitecture Task Tracker

## Task 0 — Create feature branches and task tracker

- task id: 0
- task title: Create feature branches and task tracker
- repositories affected: Community, Supported
- task type: implementation
- status: complete
- branch: feature/rearchitecture-runtime-overlay-contract
- files changed:
  - docs/internal/rearchitecture_task_tracker.md
- validation performed:
  - Confirmed v1.0.0 tag exists
  - Confirmed feature/rearchitecture-runtime-overlay-contract branch exists
  - Checked out feature/rearchitecture-runtime-overlay-contract
  - Confirmed docs/architecture/overlay_contract_v1.md exists
  - Created or updated docs/internal/rearchitecture_task_tracker.md
  - Confirmed no runtime, Docker Compose, Kubernetes, or overlay files were modified
- result: pass
- notes:
  - Branch already existed in both repositories before Task 0 execution.
  - Task 0 completed as governance/setup only.
- next task: Task 1 — Discover Community runtime and overlays

## Task 1 — Discover Community runtime and overlays

- task id: 1
- task title: Discover Community runtime and overlays
- repository: Community
- task type: discovery
- status: complete
- branch: feature/rearchitecture-runtime-overlay-contract
- report path: docs/internal/task_1_community_runtime_overlay_discovery.md
- summary of findings:
  - Base runtime is a Docker Compose stack with `minio`, `minio-init`, `airflow`, `jupyter`, and `php`.
  - Overlay evidence is Docker Compose and file-only; no Kubernetes or Helm runtime overlays were found.
  - The implemented Airflow runtime does not match the authoritative contract because it uses one `airflow` service and SQLite instead of `airflow-webserver`, `airflow-scheduler`, and PostgreSQL.
  - Repo-root `.env` contains real Kaggle credentials and violates the secrets contract.
  - Overlay directories `overlay_hello_world`, `overlay_asx_historic_csv`, `overlay_kaggle_ingestion`, `overlay_heartbeat_v2`, and `overlay_file_only_demo` are all evidenced in the repository.
- validation status:
  - Repository and branch checks passed.
  - Discovery report created.
  - No runtime or configuration files were modified.
  - `docs/architecture/master_prompt.md` is treated as allowed supervisory documentation, not a runtime/configuration file.
  - The only non-runtime changed or untracked files are `docs/internal/task_1_community_runtime_overlay_discovery.md`, `docs/internal/rearchitecture_task_tracker.md`, and `docs/architecture/master_prompt.md`.
- recommended next task: Task 2, prioritising reconciliation of the implemented Community runtime with the authoritative Airflow and secrets contract

## Task 3 — Compare Community and Supported runtime discovery findings

- task id: 3
- task title: Compare Community and Supported runtime discovery findings
- repositories compared: Community and Supported
- task type: documentation / analysis
- status: complete
- branch: feature/rearchitecture-runtime-overlay-contract
- report path:
  - docs/internal/task_3_runtime_comparison_and_canonical_findings.md
- summary of canonical findings:
  - Filesystem-first overlay surfaces are common across both repositories and are canonical now.
  - Split Airflow services are the canonical target; Community's single logical `airflow` service and Supported's logical-overlay compatibility path are legacy.
  - Supported Compose remains non-compliant because Airflow metadata still uses SQLite; PostgreSQL-backed Compose design is the next required design step.
  - Compose must be reconciled before any Kubernetes overlay design proceeds.
  - Overlay service mutation should be minimized so overlays remain primarily filesystem-first rather than service-redefinition-heavy.
- validation status:
  - Community and Supported repository paths verified.
  - Both repositories verified on branch `feature/rearchitecture-runtime-overlay-contract`.
  - Required inputs confirmed present in both repositories.
  - Analysis constrained to the authoritative contract, Task 1 report, Task 2 report, and task trackers.
  - Only Task 3 report and task tracker documentation files were updated.
- recommended next task:
  - Task 4 — Design the Supported Compose PostgreSQL replacement and related Compose-side contract reconciliation

## Task 8 — Discover Community vs Supported runtime gaps (delta analysis)

- task id: 8
- task title: Discover Community vs Supported runtime gaps (delta analysis)
- repositories affected: Community, Supported
- task type: discovery / analysis
- status: blocked
- branch: feature/rearchitecture-runtime-overlay-contract
- report path:
  - docs/internal/task_8_community_supported_delta_analysis.md
- summary of key deltas:
  - Community still exposes one logical `airflow` service, while the Supported canonical runtime requires explicit `airflow-webserver` and `airflow-scheduler`.
  - Community still uses SQLite metadata and an `airflow-db` model, while the Supported canonical runtime now treats PostgreSQL-backed Airflow metadata as the aligned baseline.
  - Community overlays still target logical `airflow` and therefore do not align to the current explicit-service overlay contract surface.
  - Community still carries hidden coupling through repo-root `.env`, real credentials, implicit overlay env assumptions, wrapper-path differences, and service-mutation-heavy overlays.
  - Community validation expectations remain tied to the legacy runtime surface instead of the current split-service and invalid-legacy-overlay failure model.
- validation result:
  - blocked
- validation performed:
  - Confirmed Community and Supported repository paths and branch.
  - Confirmed required Task 1, Task 2, Task 3, contract, and tracker inputs exist.
  - Limited analysis to the specified documents plus Supported tracker evidence for the now-canonical Supported state.
  - Created Task 8 delta report without modifying runtime or configuration files.
  - Final repository-state validation failed because pre-existing non-Task-8 files were already changed or untracked in both repositories.
- recommended next task:
  - Task 9 — define and execute Community alignment work using the Task 8 blocker and high-severity deltas as scope

## Task 9 — Design Community alignment to canonical runtime

- task id: 9
- task title: Design Community alignment to canonical runtime
- repository: Community
- task type: design
- status: blocked
- branch: feature/rearchitecture-runtime-overlay-contract
- design doc path:
  - docs/internal/task_9_community_alignment_design.md
- summary of design approach:
  - Defines a four-stage Community-only alignment plan covering runtime foundation, overlay targeting, environment and secrets cleanup, and validation alignment.
  - Commits Community to the canonical Airflow topology of `airflow-postgres`, `airflow-user-init`, `airflow-webserver`, and `airflow-scheduler`, with removal of SQLite and no logical `airflow` compatibility surface.
  - Requires Community overlays to migrate off `services.airflow`, converge packaged and dev targeting semantics, and fail when they still depend on legacy logical `airflow`.
  - Tightens the environment model so real credentials are removed, placeholders are used in versioned examples, and runtime and overlay env assumptions become explicit.
  - Defines aligned PASS/FAIL validation based on Compose startup, Airflow health, valid overlay execution, and intentional failure of invalid legacy overlays.
- validation status:
  - blocked
- validation performed:
  - Confirmed Community and Supported repository paths and branch.
  - Limited review to the specified Task 1, Task 8, Task 3, Task 4, and contract documents only.
  - Created the Task 9 design document and updated the task tracker without modifying runtime or configuration files.
  - Final repository-state validation remains blocked because Community also contains pre-existing untracked files outside the Task 9 output set.
- recommended next task:
  - Implement Community Stage 1 only: replace the single logical `airflow` runtime with `airflow-postgres`, `airflow-user-init`, `airflow-webserver`, and `airflow-scheduler`, and remove SQLite before overlay migration begins.
