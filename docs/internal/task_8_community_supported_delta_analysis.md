# Task 8 — Community vs Supported Delta Analysis

## 1. Scope

This report defines the evidence-based delta between the current Community runtime and the now-canonical Supported runtime/contract state on branch `feature/rearchitecture-runtime-overlay-contract`.

This task is analysis only. It does not propose implementation design, modify runtime files, or change prior task reports.

## 2. Inputs Reviewed

- Community: `docs/internal/task_1_community_runtime_overlay_discovery.md`
- Community: `docs/internal/rearchitecture_task_tracker.md`
- Supported: `docs/internal/task_2_supported_runtime_overlay_discovery.md`
- Supported: `docs/internal/task_3_runtime_comparison_and_canonical_findings.md`
- Supported: `docs/internal/rearchitecture_task_tracker.md`
- Supported: `docs/architecture/overlay_contract_v1.md`

## 3. Executive Summary

Community remains structurally close to the shared overlay filesystem model, but it is materially behind the Supported canonical runtime in the areas that now define contract compliance: explicit split Airflow services, PostgreSQL metadata, removal of logical `airflow` compatibility, and explicit overlay targeting against real base-runtime services.

The largest gaps are not cosmetic. Community still depends on one logical `airflow` service, SQLite metadata, overlay files that target that logical service, wrapper flows that assume that service model, and inherited environment/default-value behaviour that is looser than the current Supported contract direction.

The exact alignment question for Task 8 therefore resolves to this: Community must stop behaving like a single-service Airflow runtime with overlay-era compatibility assumptions and instead expose the same contract surface that Supported now treats as canonical.

## 4. Delta by Category

### 4.1 Airflow Service Model

- Community current state: base Compose exposes one logical `airflow` service and Task 1 records that overlays are authored against that service.
- Supported canonical state: the authoritative contract requires `airflow-webserver` and `airflow-scheduler`, and the Supported tracker records that the logical `airflow` compatibility path was removed.
- Gap description: Community does not expose the required Airflow contract surface and still centers runtime and overlay behaviour on a non-contract service name.
- Severity: BLOCKER
- Change type: structural, behavioural

### 4.2 Metadata Database

- Community current state: Task 1 records SQLite metadata via `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: sqlite:////opt/airflow/airflow.db` and an `airflow-db` volume.
- Supported canonical state: the contract requires PostgreSQL for Supported, and the Supported tracker records that Compose now uses PostgreSQL-backed Airflow metadata and removed the SQLite-oriented volume.
- Gap description: Community still uses the legacy metadata model and therefore does not align to the canonical runtime baseline that now excludes SQLite.
- Severity: BLOCKER
- Change type: structural, configuration

### 4.3 Docker Compose Structure

- Community current state: base services are `minio`, `minio-init`, `airflow`, `jupyter`, and `php`, with no split Airflow init/database structure.
- Supported canonical state: Supported tracker entries show a Compose model that includes explicit split Airflow services and a dedicated Airflow PostgreSQL service.
- Gap description: Community Compose structure is missing the canonical Airflow-related service layout and still models Airflow as one combined container.
- Severity: BLOCKER
- Change type: structural

### 4.4 Wrapper Script Behaviour

- Community current state: `start-compose.sh` and `stop-compose.sh` resolve `--overlay` files against a base runtime that still expects logical `airflow`; packaged heartbeat flow can start without `--overlay`.
- Supported canonical state: the contract still permits `./start-<runtime>.sh --overlay <overlay>`, but the Supported tracker records that wrapper-script compatibility for logical `airflow` was removed and legacy overlays are expected to fail rather than be adapted.
- Gap description: Community wrapper behaviour still operates in a legacy service model and still tolerates activation paths that are inconsistent with the canonical explicit-service surface.
- Severity: HIGH
- Change type: behavioural

### 4.5 Overlay Targeting Model

- Community current state: Task 1 records overlay Compose files that override `airflow`, `jupyter`, and `php`, and notes that overlay authoring assumes the base `airflow` service exists.
- Supported canonical state: the contract requires overlays to target explicit base-runtime services such as `airflow-webserver` and `airflow-scheduler`, and the Supported tracker records that active overlay files were migrated off `services.airflow`.
- Gap description: Community overlays target a service abstraction that is no longer part of the canonical runtime contract.
- Severity: BLOCKER
- Change type: structural, behavioural

### 4.6 Overlay File Structure

- Community current state: overlay directory structures strongly align to the standard filesystem surfaces, but Task 1 records drift between dev overlay activation and packaged overlay activation, especially for `overlay_heartbeat_v2`.
- Supported canonical state: Task 3 identifies the filesystem-first overlay surface as canonical, while the contract requires activation through the base start script with optional overlay YAML only.
- Gap description: Community overlay folders are broadly aligned, but packaged-versus-dev activation semantics still drift and some packaged flows rely on copied files rather than the same explicit activation model.
- Severity: MEDIUM
- Change type: behavioural

### 4.7 Environment and Secrets

- Community current state: Task 1 records heavy reliance on repo-root `.env`, embedded default credentials in Compose, undeclared overlay env assumptions, and a repo-root `.env` containing real Kaggle credentials.
- Supported canonical state: the contract requires runtime secret injection and forbids real credentials in overlays; the current Supported direction is placeholder/runtime-variable based rather than committed real secrets.
- Gap description: Community is not aligned to the canonical secret and environment discipline because it contains real credentials in the active runtime path and leaves several overlay requirements implicit.
- Severity: BLOCKER
- Change type: configuration, behavioural

### 4.8 Dependency Model

- Community current state: Task 1 records mixed dependency delivery through baked Dockerfiles plus `PIP_ADDITIONAL_REQUIREMENTS`, overlay-specific Dockerfiles, and implicit inherited package assumptions.
- Supported canonical state: the contract allows base-runtime shared dependencies and explicit overlay extension, but not dependency inference from overlay filesystem contents; Task 3 treats implicit inheritance and runtime mutation as drift, not as canonical behaviour.
- Gap description: Community remains only partially aligned because dependency expectations are split across images, runtime mutation, and undeclared inheritance.
- Severity: HIGH
- Change type: configuration

### 4.9 Runtime Behaviour

- Community current state: Airflow is launched as one combined command path, overlays rely on that combined runtime shape, and packaged/source-tree overlay activation is not fully uniform.
- Supported canonical state: the canonical behaviour is explicit split-service runtime execution, explicit-service overlay targeting, and no logical-`airflow` adaptation layer.
- Gap description: Community runtime behaviour still depends on legacy combined-service execution and overlay assumptions that the canonical runtime has already removed.
- Severity: BLOCKER
- Change type: behavioural

### 4.10 Validation Model

- Community current state: Task 1 records contract non-compliance for Airflow service names and metadata database, but does not show a validation model based on explicit split-service health and failure of invalid legacy overlay targeting.
- Supported canonical state: Supported tracker validation after Tasks 5 and 6 explicitly checks PostgreSQL-backed Airflow startup, split-service health, and failure of legacy logical `airflow` overlays.
- Gap description: Community validation expectations are still anchored to the old runtime surface and do not yet match the canonical pass/fail conditions.
- Severity: HIGH
- Change type: behavioural

## 5. Hidden Coupling Risks

Hidden coupling to be removed:

- Community reliance on logical `airflow` as the overlay and runtime anchor.
- Community reliance on SQLite metadata as part of normal Airflow startup assumptions.
- Community reliance on implicit env vars that are used by overlays and scripts but not surfaced as a strict explicit runtime contract.
- Community reliance on wrapper script magic and packaging-path differences to make overlay activation work across dev and packaged modes.
- Community reliance on overlay service mutation rather than keeping overlays primarily filesystem-first with only narrow explicit service overrides.

Additional hidden coupling observations:

- Overlay dependency assumptions are partly inherited from whichever Airflow or Jupyter image happens to be selected, rather than from one explicit canonical declaration model.
- Packaged overlays that start without `--overlay` after copy/unzip create a second behavioural path that is easy to misread as equivalent to explicit overlay activation.

## 6. Alignment Scope

### 6.1 Phase A — Runtime Correctness

What MUST change in Community to align:

- Replace the single logical `airflow` runtime surface with the explicit split Airflow service model.
- Remove SQLite as the Community Airflow metadata runtime assumption and align metadata expectations with the canonical PostgreSQL-backed model.
- Eliminate Community overlay dependence on `services.airflow`.
- Eliminate Community runtime behaviour that depends on combined Airflow execution in one container/service path.
- Remove real credentials from the active Community runtime path and stop treating repo-committed `.env` values as a valid secret source.

### 6.2 Phase B — Contract Compliance

What MUST change in Community to align:

- Make overlay runtime targeting reference only services that exist in the canonical base runtime.
- Tighten wrapper and activation semantics so Community does not depend on legacy compatibility assumptions or inconsistent packaged-vs-dev activation behaviour.
- Make required overlay/runtime environment inputs explicit enough that overlays no longer rely on undocumented inherited variables.
- Reduce Community dependence on runtime dependency mutation and undeclared package inheritance where those assumptions affect overlay portability and contract clarity.
- Align Community validation expectations to the canonical split-service and PostgreSQL-backed runtime surface.

### 6.3 Phase C — Optional Alignment

What MAY change in Community for closer parity:

- Reduce remaining service-mutation-heavy overlay patterns where filesystem-first overlay behaviour is already sufficient.
- Normalize packaged and source-tree overlay activation language so documentation and behaviour read as one model.
- Tighten low-value default credential examples that are placeholders but still broader than necessary.

## 7. Risks and Unknowns

- This analysis is intentionally limited to the specified discovery reports, the authoritative contract, and task-tracker evidence. It does not re-inspect Community or Supported runtime files directly.
- Supported Task 2 and Task 3 document pre-alignment drift; Supported tracker entries for Tasks 5, 6, and 7 are the documentary evidence used for the current canonical state.
- Community may contain additional downstream assumptions in docs or tooling that were not reopened for this task because Task 8 was constrained to the specified inputs.
- Packaged overlay activation semantics remain a shared area of historical drift, but only the Community alignment delta is in scope here.

## 8. Recommended Next Task

Task 9 should convert this delta into a Community-only alignment plan or implementation scope focused first on runtime correctness blockers: explicit Airflow services, metadata backend alignment, overlay targeting removal of logical `airflow`, and secret/env contract cleanup.

## 9. Validation Evidence

- Community repository path verified: `/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community`
- Supported repository path verified: `/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-supported`
- Both repositories verified on branch `feature/rearchitecture-runtime-overlay-contract`
- Required inputs confirmed present before analysis
- Analysis inputs limited to:
  - `docs/internal/task_1_community_runtime_overlay_discovery.md`
  - `docs/internal/task_2_supported_runtime_overlay_discovery.md`
  - `docs/internal/task_3_runtime_comparison_and_canonical_findings.md`
  - `docs/architecture/overlay_contract_v1.md`
  - `docs/internal/rearchitecture_task_tracker.md`
- Supported canonical-state evidence taken from completed Task 5, Task 6, Task 6.1, and Task 7 entries in `docs/internal/rearchitecture_task_tracker.md`
- Final repository validation result: blocked
- Community `git status --short` included pre-existing untracked documentation outside the two Task 8 target paths
- Supported `git status --short` and `git diff --name-only` included pre-existing runtime and documentation changes outside the two Task 8 target paths
- This task itself created or updated documentation only
