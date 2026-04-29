You are acting as supervisor for a controlled rearchitecture of Docker Compose and Kubernetes configuration across two repositories.

Repositories:

Community repo:
/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community

Supported repo:
/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-supported

Current stable baseline:

Both repositories are tagged v1.0.0. The v1.0.0 tag represents the known working baseline. Do not rewrite history or alter that baseline.

Working branches:

All work must be carried out in feature branches in both repositories.

Community branch:
feature/rearchitecture-runtime-overlay-contract

Supported branch:
feature/rearchitecture-runtime-overlay-contract

Purpose:

We are rearchitecting the Docker Compose and Kubernetes runtime configuration so both repositories consistently support the Open Data Lake overlay contract.

The end target is a Kubernetes overlay design, but Kubernetes overlay support must not be introduced until the existing Docker and Kubernetes baselines are clarified, cleaned, and validated.

Core overlay contract:

The overlay contract is defined in:
docs/architecture/overlay_contract_v1.md

You must read this file before performing any task and treat it as the authoritative source of truth.

Contract version: v1.0.0

Do not modify the contract during implementation tasks.
If a change is required, raise it explicitly as a separate task.

Airflow contract:

All supported runtime environments must use proper split Airflow services:

airflow-webserver
airflow-scheduler

The logical airflow wrapper service is not part of the core contract.

SQLite is not part of the Supported runtime target. Supported Docker and Supported Kubernetes should use PostgreSQL for Airflow metadata.

Secrets contract:

Overlays must not include real secrets. They may include placeholders or examples only. Runtime environments are responsible for secret injection.

Dependency contract:

Base images should provide standard dependencies required by common overlays. Overlay-specific dependencies must be explicit via runtime configuration or image extension and must not be silently inferred.

Core planning constraint:

This is a long-running supervised programme of work. Do not jump ahead. Each task must be discovery, implementation, or testing. Discovery tasks must not modify implementation files. Implementation tasks must include validation. Testing tasks must produce clear pass/fail evidence.

Scope:

There are two repositories:

1. Community repo:
- Docker Compose runtime only
- base functionality
- five overlays to validate against Docker Compose

2. Supported repo:
- Docker Compose runtime
- Kubernetes runtime
- base functionality
- five overlays to validate against Docker Compose and Kubernetes

The five overlays must be discovered from the repositories and tested explicitly. Do not assume their exact names without repository inspection.

Required management artefact:

Maintain a task tracker at:

docs/internal/rearchitecture_task_tracker.md

The tracker must include:

- task id
- task title
- repository or repositories affected
- task type: discovery, implementation, testing, documentation
- status: not started, in progress, blocked, complete
- branch
- files changed
- validation performed
- result
- notes
- next task

General rules:

- Do not modify files unless the current task explicitly allows implementation.
- Do not create Kubernetes overlay support until the existing Docker and Kubernetes baselines are validated.
- Do not invent functionality.
- Do not delete existing working functionality without explicit instruction.
- Preserve the v1.0.0 baseline.
- Work in feature branches only.
- Keep changes small and staged by task.
- At the end of every task, report:
  - current branch
  - git status
  - files changed
  - tests or validation run
  - result
  - recommended next task
- Do not commit unless explicitly instructed.

Initial task list:

Task 0 — Create feature branches and task tracker
Create or verify the feature branch in both repositories. Create the rearchitecture task tracker. Do not change runtime implementation.

Task 1 — Discover current runtime and overlay structure in Community
Document the Community Docker Compose runtime, base folders, scripts, overlays, overlay YAML, service mounts, environment variables, and current test/start workflow.

Task 2 — Discover current runtime and overlay structure in Supported
Document the Supported Docker Compose runtime, Kubernetes runtime, base folders, scripts, overlays, overlay YAML, service mounts, environment variables, and current test/start workflow.

Task 3 — Compare Community and Supported runtime contracts
Identify differences between Community Docker, Supported Docker, and Supported Kubernetes. Classify each difference as intentional, accidental, historical, or unresolved.

Task 4 — Define canonical base runtime contract
Document the agreed base runtime contract for installation folders, service names, Airflow model, PostgreSQL usage, MinIO zones, PHP route behaviour, secrets, and dependency expectations.

Task 5 — Validate Community Docker base runtime
Run and document validation of the Community Docker Compose base runtime without overlays.

Task 6 — Validate Community Docker overlays
Test each discovered Community overlay against Community Docker Compose. Record pass/fail evidence and required fixes.

Task 7 — Validate Supported Docker base runtime
Run and document validation of the Supported Docker Compose base runtime without overlays.

Task 8 — Validate Supported Docker overlays
Test each discovered Supported overlay against Supported Docker Compose. Record pass/fail evidence and required fixes.

Task 9 — Validate Supported Kubernetes base runtime
Run and document validation of the Supported Kubernetes base runtime without overlays.

Task 10 — Remediate runtime drift
Implement only the minimum required fixes to align Community Docker, Supported Docker, and Supported Kubernetes with the canonical base runtime contract.

Task 11 — Retest remediated Docker runtimes
Retest Community Docker base and overlays, then Supported Docker base and overlays.

Task 12 — Retest remediated Supported Kubernetes base runtime
Retest Supported Kubernetes base runtime after remediation.

Task 13 — Design Kubernetes overlay support
Only after Tasks 1–12 are complete, design the Kubernetes overlay model using PVC-backed standard installation folders and Kustomize-compatible runtime patches.

Task 14 — Implement Kubernetes overlay support
Implement Kubernetes overlay support in Supported only, following the approved design.

Task 15 — Test Supported Kubernetes overlays
Test each overlay against the Supported Kubernetes runtime.

Task 16 — Final documentation and release candidate
Update README, RUNBOOK, overlay contract documentation, and validation reports. Prepare release candidate notes.

Current task:

Task 0 — Create feature branches and task tracker