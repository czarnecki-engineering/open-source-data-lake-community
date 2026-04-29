# Task 3 — Runtime Comparison and Canonical Findings

## 1. Scope

This report compares the Community and Supported runtime discovery findings against the authoritative contract in `docs/architecture/overlay_contract_v1.md`.

It is limited to evidence from:

- `docs/architecture/overlay_contract_v1.md`
- `docs/internal/task_1_community_runtime_overlay_discovery.md`
- `docs/internal/task_2_supported_runtime_overlay_discovery.md`
- `docs/internal/rearchitecture_task_tracker.md`

This report is analytical only. It does not implement runtime changes. Kubernetes overlay design remains out of scope.

## 2. Inputs Reviewed

- Community: `docs/architecture/overlay_contract_v1.md`
- Community: `docs/internal/task_1_community_runtime_overlay_discovery.md`
- Community: `docs/internal/rearchitecture_task_tracker.md`
- Supported: `docs/architecture/overlay_contract_v1.md`
- Supported: `docs/internal/task_2_supported_runtime_overlay_discovery.md`
- Supported: `docs/internal/rearchitecture_task_tracker.md`

## 3. Executive Summary

Both repositories share the same filesystem-first overlay direction and the same standard runtime surfaces: `config/`, `dags/`, `notebooks/`, `scripts/`, `data/`, and `php/`. Both also use Docker Compose wrapper scripts and repository overlay folders as the active overlay mechanism. That common shape is the strongest current evidence of what is already canonical.

The main divergence is Airflow and runtime maturity. Community still operates as a legacy single logical `airflow` service backed by SQLite. Supported has moved further toward the contract by splitting Compose into `airflow-webserver` and `airflow-scheduler`, but it still keeps SQLite in Compose and still carries compatibility handling for legacy logical `airflow` overlays. Supported also contains Kubernetes runtime material, but the contract evidence and the Task 2 findings show that Compose still has unresolved drift and remains the practical source of truth for the current overlay model comparison.

The canonical direction supported by the evidence is: filesystem-first overlays, split Airflow services, PostgreSQL-backed Airflow metadata in Supported, minimal overlay service mutation, and removal of logical `airflow` overlay targeting. The next design task should therefore be design of the Supported Compose PostgreSQL replacement and associated Compose-side contract reconciliation. Kubernetes overlay work must not begin yet.

## 4. Runtime Architecture Comparison

Common runtime surfaces across both repos:

- Docker Compose is an active runtime surface.
- Root `start-compose.sh` and `stop-compose.sh` wrappers are the runtime activation path.
- Overlay source trees use `overlay_<name>/` folders.
- Packaged overlay runtime folders and overlay zip packaging exist.
- Standard contract folders are present and used as overlay surfaces.
- Operational overlays are Compose overlays or file-only overlays.

Differences between repos:

| Area | Community | Supported | Comparative finding |
| --- | --- | --- | --- |
| Base Compose entry point | Single base Compose stack | Single base Compose stack with more services | Common model, Supported is broader operationally |
| Start/stop wrapper behaviour | Resolves overlay files and starts selected Compose layers | Same, plus compatibility shim for logical `airflow` overlays | Supported inherits Community-style wrapper model and adds transitional compatibility logic |
| Runtime folders | Standard contract folders plus overlay folders | Same, plus `k8s/` and `.k8s-runtime/` evidence | Filesystem runtime surface is common; Kubernetes is additional Supported-only runtime evidence |
| Service list | `minio`, `minio-init`, `airflow`, `jupyter`, `php` | `minio`, `minio-init`, `airflow-user-init`, `airflow-webserver`, `airflow-scheduler`, `jupyter`, `cloudbeaver`, `streamlit`, `ollama`, `php` | Supported shows lineage beyond Community with split Airflow and a larger service footprint |
| Kubernetes presence | No runtime Kubernetes overlays found | Active Kubernetes runtime evidence present | Kubernetes exists only in Supported and is not yet canonical for overlay design |
| Operational source of truth | Base Compose runtime and overlay Compose files | Task 2 describes base Supported Compose as behavioural source of truth despite Kubernetes presence | Compose remains the surface that must be reconciled first |
| Packaged overlay behaviour | Mixed dev overlay Compose activation and packaged copy/unzip activation | Same pattern, plus compatibility support for older logical overlay targeting | Source-tree and packaged overlay behaviour still drift in both repos |

Inferred lineage:

- Supported appears to be a later evolution of the same Compose-and-overlay model found in Community.
- Supported preserves the Community overlay activation style while partially moving toward the contract through split Airflow services.
- The compatibility shim in Supported is strong evidence that legacy Community-era logical overlay assumptions are still being carried forward.

Current architectural direction inferred from evidence:

- The shared filesystem overlay surface is stable.
- Compose remains the decisive near-term runtime design surface.
- Supported is moving toward the contract, but the move is incomplete.

## 5. Airflow Model Comparison

| Area | Community | Supported | Assessment |
| --- | --- | --- | --- |
| Logical service model | Single logical `airflow` service | Split `airflow-webserver` and `airflow-scheduler` in base Compose, but logical `airflow` still exists in overlay behaviour | Split service model is the canonical candidate; logical `airflow` is legacy |
| Metadata DB | SQLite | SQLite in Compose, PostgreSQL in Kubernetes | Community non-compliant; Supported partially compliant overall but non-compliant in Compose |
| Overlay targeting | Overlays assume logical `airflow` | Many overlay Compose files still target logical `airflow`; wrapper shim adapts them | Legacy behaviour in both repos |
| Alignment to contract | Not compliant | Partially compliant overall | Supported is closer, but not yet contract-compliant end to end |

Classification against the Airflow contract:

- Community single logical `airflow` service: non-compliant, legacy.
- Community SQLite metadata: non-compliant, legacy.
- Supported split `airflow-webserver` and `airflow-scheduler` in Compose: compliant, canonical candidate.
- Supported SQLite in Compose: non-compliant, legacy.
- Supported PostgreSQL in Kubernetes: compliant in isolation, but not yet canonical for this task because Compose remains unresolved.
- Supported compatibility shim for logical `airflow` overlays: partially compliant operational bridge, transitional legacy rather than canonical.

Airflow comparison conclusion:

- The contract direction is clear: split Airflow services and PostgreSQL metadata.
- Community is entirely behind that target.
- Supported contains the clearest canonical service topology, but still violates the contract through SQLite and overlay compatibility shims.

## 6. Overlay Model Comparison

Common overlay pattern:

- Overlay content is organized in `overlay_<name>/` trees.
- Overlay contents map onto the contract folders.
- Dev overlays use Compose activation.
- Packaged overlays assume copy/unzip merge semantics into the installation root.
- File-only overlays are evidenced and valid under the contract.

Key differences and drift:

| Area | Community | Supported | Finding |
| --- | --- | --- | --- |
| Overlay directory structure | Strong alignment to contract folders | Same | Common and likely canonical |
| Overlay activation method | Base wrapper plus `--overlay` Compose layers | Same | Common and likely canonical |
| Dev vs packaged overlays | Some packaged overlays start without `--overlay` after files are copied into base surfaces | Same general pattern | Shared drift between source-tree and packaged activation |
| File-only overlays | Explicitly evidenced | Explicitly evidenced | Canonical candidate because contract allows all folders to be optional |
| Compose overlay behaviour | Limited service overrides around logical `airflow`, `jupyter`, `php` | Similar but broader drift because overlays still target logical `airflow` against split base runtime | Supported exposes the sharper contract mismatch |
| Overlay service override pattern | Service mutation exists but is still close to development convenience | Often exceeds minimal env/service override intent by changing builds, images, and volumes | Service mutation should be minimized before further runtime expansion |
| Kubernetes overlays | No operational Kubernetes overlays found | `k8s/overlays/minikube` and cloud placeholder exist | Not canonical for overlay contract design yet |

Overlay comparison conclusion:

- The filesystem overlay surface is the common canonical core.
- Compose overlay files are presently a convenience/compatibility layer, not a clean canonical contract surface.
- The biggest overlay drift is continued logical `airflow` targeting plus heavier service mutation than the contract intends.
- Compose must be reconciled before Kubernetes overlays are introduced or designed further.

## 7. Environment and Secrets Comparison

| Area | Community | Supported | Finding |
| --- | --- | --- | --- |
| `.env.example` | Present and treated as placeholder/default file | Present and treated as placeholder/default file | Common practice and acceptable in principle |
| `.env` assumptions | Root `.env` expected by Compose wrappers; real Kaggle credentials were found in Community `.env` | Root `.env` expected by Compose wrappers; no clear real secrets reported in inspected Supported files | Hidden `.env` dependency is common; Community shows a direct governance breach |
| Placeholder vs real secrets | Overlay examples mostly placeholders; repo-root `.env` contains real Kaggle credentials | No clear real secrets in overlay files, but many concrete default credentials appear in versioned files | Community has a stronger immediate violation; Supported remains only partially aligned |
| Hard-coded defaults | Weak demo defaults present | Weak demo defaults present broadly | Common drift from placeholder-only intent |
| Kubernetes secret manifests | Not applicable from Community discovery | Present, with literal development credentials in `stringData` per Task 2 | Additional Supported-only governance concern |
| Overlay-specific credentials | Kaggle examples rely on external env discipline | Same, plus wider default-value spread | Both rely on inherited env assumptions |
| Duplicate env vars and inherited assumptions | Present | Present | Both repos rely on repeated and inherited runtime variables |

Secrets contract assessment:

- Community: non-compliant in practice because real Kaggle credentials were found in repo-root `.env`.
- Supported: partially compliant because no clear real overlay secrets were found, but placeholder-only discipline is not consistently maintained.

What must be fixed later, without implementing it now:

- Remove real credential usage from active local runtime assumptions.
- Replace concrete default credential values with clearer placeholder-only examples where the contract requires placeholders.
- Reduce hidden inherited env assumptions so overlay requirements are explicit.

## 8. Dependency Model Comparison

| Area | Community | Supported | Finding |
| --- | --- | --- | --- |
| Base image dependency strategy | Base Airflow and Jupyter Dockerfiles provide shared packages | Same, with additional base images for CloudBeaver and Streamlit plus separate Kubernetes images | Shared dependency baking is common and mostly aligned |
| Overlay-specific Dockerfiles | Present for major overlays | Present for major overlays | Common pattern and acceptable when explicit |
| Runtime `pip install` / mutable dependency injection | Base Compose uses `PIP_ADDITIONAL_REQUIREMENTS` alongside baked images | Same pattern, plus Kubernetes Streamlit startup-time install noted in Task 2 | Mixed runtime/image dependency models are a shared drift |
| Implicit inheritance | Overlays may bypass base image assumptions unless they reproduce needed packages | Same, plus some overlays explicitly reuse base images and rely on inherited dependencies | Implicit inheritance remains unresolved in both repos |
| Lockfiles / reusable manifests | Not evidenced in Task 1 findings | Not evidenced in Task 2 findings | Weakness in both repos |
| Compose vs Kubernetes image strategy | Community has Compose-only evidence | Supported has different Compose and Kubernetes image strategies | Supported introduces additional dependency drift across runtime implementations |

Dependency contract assessment:

- Shared dependencies in base images appear to be the intended canonical direction.
- Overlay-specific dependencies are acceptable when explicitly declared.
- Implicit inheritance, runtime `pip install`, and lack of stronger reusable dependency manifests remain non-canonical drift.

## 9. Contract Compliance Matrix

| Contract area | Community | Supported | Canonical reading from Task 3 |
| --- | --- | --- | --- |
| Standard installation folders exposed | compliant | compliant | Canonical now |
| Filesystem-first overlay model | compliant structurally | compliant structurally | Canonical now |
| Overlay copy/unzip merge semantics | compliant | compliant | Canonical now |
| Base activation via `start-<runtime>.sh --overlay` | partially compliant because packaged behaviour sometimes bypasses `--overlay` after copy/unzip | partially compliant for same reason | Canonical direction, but activation semantics need clarification |
| Airflow split services required | non-compliant | compliant at base Compose layer | Split services are canonical |
| No logical `airflow` service abstraction | non-compliant | partially compliant because overlays still depend on it | Logical `airflow` is legacy |
| PostgreSQL required for Airflow metadata in Supported | non-compliant by contract direction | non-compliant in Compose, compliant in Kubernetes | Supported Compose must be reconciled before further design |
| SQLite prohibited in Supported runtime | legacy pattern aligned with Community implementation but not contract | non-compliant in Compose | SQLite is legacy |
| Overlay YAML limited to env/service-specific overrides | partially compliant | partially compliant | Heavy service mutation is not canonical |
| No real secrets in overlays/runtime examples | non-compliant in practice due to Community `.env` evidence | partially compliant | Placeholder-only examples remain the contract target |
| Runtime independence across Compose/Kubernetes/future | not yet challenged because Community is Compose-only | partially compliant but divergent between Compose and Kubernetes | Kubernetes overlay design must wait until Compose is reconciled |

## 10. Canonical Findings

### 10.1 Canonical Now

- The standard overlay filesystem surfaces `config/`, `dags/`, `notebooks/`, `scripts/`, `data/`, and `php/`.
- Overlay packaging as copy/unzip merge into the installation root.
- Repository-local overlay development under `overlay_<name>/`.
- Root runtime wrapper scripts as the activation entry point for Compose-based development and testing.
- File-only overlays as a valid overlay form when no runtime mutation is required.
- Split Airflow services as the canonical target service model, based on the contract and Supported base Compose evidence.

### 10.2 Legacy / To Be Removed

- Single logical `airflow` runtime service.
- Overlay Compose files that target logical `airflow`.
- Supported wrapper compatibility shim for logical `airflow` overlays, once migration is designed and completed.
- SQLite-backed Airflow metadata as a runtime target.
- Concrete default credentials presented as if they were acceptable long-term runtime configuration.

### 10.3 Requires Design Decision

- Exact Compose-side design for replacing Supported Airflow SQLite with PostgreSQL.
- Exact migration path from logical `airflow` overlay targeting to explicit split-service semantics without widening overlay complexity.
- How packaged overlay activation should be described so source-tree and copy/unzip modes are conceptually consistent.
- The minimal allowable scope of overlay service overrides so overlays remain filesystem-first rather than service-redefinition-heavy.
- How Compose and Kubernetes should eventually align on naming and dependency strategy after Compose is reconciled.

### 10.4 Requires Implementation Later

- Update Supported Compose to use PostgreSQL for Airflow metadata.
- Update Community runtime model toward split Airflow semantics if Community is to remain aligned with the authoritative contract.
- Remove logical `airflow` assumptions from overlay Compose files.
- Reduce inherited env assumptions and convert secret examples toward placeholder-only governance.
- Tighten dependency declaration so overlay requirements are explicit and not dependent on incidental base-image inheritance or runtime `pip install` behaviour.

### 10.5 Must Not Be Done Yet

- Kubernetes overlay design or implementation.
- New Kubernetes overlay contracts.
- Further runtime expansion that assumes the current Compose overlay behaviour is already canonical.
- Implementation work based on logical `airflow` compatibility as if it were a permanent contract surface.

## 11. Risks and Open Questions

- The contract is clearer than the current implementations, but not all runtime behaviours have yet converged on it.
- Supported contains two runtime directions at once: Compose as behavioural source of truth and Kubernetes as a partially more contract-aligned runtime for Airflow metadata.
- Community and Supported both show drift between source-tree overlay activation and packaged overlay activation semantics.
- Secrets governance is weaker in Community because real credentials were reported in `.env`, but Supported also carries non-placeholder development credentials in versioned configuration.
- Documentation authority remains sensitive where repository-local overlay guidance overlaps with the authoritative contract.

## 12. Recommended Next Task

Task 4 should be design of the Supported Compose PostgreSQL replacement.

Reasoning:

- Supported Compose is the closest runtime to the contract while still carrying a direct Airflow metadata breach.
- Supported Compose is described in Task 2 as the behavioural source of truth, so resolving it is the highest-value design step before any broader implementation work.
- Logical `airflow` overlay migration depends on clarifying the Supported Compose target first.
- Kubernetes overlay design remains out of scope until Compose-side contract drift is reconciled.

## 13. Validation Evidence

- Community repository verified at `/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community`
- Supported repository verified at `/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-supported`
- Both repositories verified on branch `feature/rearchitecture-runtime-overlay-contract`
- Inputs confirmed present before analysis
- Analysis limited to the authoritative contract, Task 1 report, Task 2 report, and task trackers
- This report introduces documentation changes only
