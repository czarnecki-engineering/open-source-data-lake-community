# Task 9 — Community Alignment Design

## 1. Scope

This document defines the safest minimal staged design to align the Community runtime with the canonical runtime contract established in Supported and codified in `docs/architecture/overlay_contract_v1.md`.

In scope:
- design for replacing the Community single-service Airflow model with explicit `airflow-webserver` and `airflow-scheduler`
- design for removing SQLite from the Community Airflow metadata path
- design for aligning Community overlays to target only canonical base-runtime services
- design for cleaning up Community environment and secrets handling
- design for Community validation criteria after alignment

Out of scope:
- implementation changes to Compose files, wrapper scripts, Dockerfiles, overlays, DAGs, notebooks, configs, Kubernetes files, or the contract
- rewriting prior task reports
- any later task execution

## 2. Inputs Reviewed

- Community:
  - `docs/internal/task_1_community_runtime_overlay_discovery.md`
  - `docs/internal/task_8_community_supported_delta_analysis.md`
- Supported:
  - `docs/internal/task_3_runtime_comparison_and_canonical_findings.md`
  - `docs/internal/task_4_supported_compose_postgres_design.md`
  - `docs/architecture/overlay_contract_v1.md`

## 3. Design Principles

- Contract-first alignment. Task 3 and the authoritative contract establish the canonical target as filesystem-first overlays, explicit `airflow-webserver` and `airflow-scheduler`, no logical `airflow`, and PostgreSQL-backed Airflow metadata for the aligned runtime direction.
- Minimal blast radius. Task 8 shows the highest-severity gaps are runtime topology, metadata backend, overlay targeting, and secrets discipline; the design should change those surfaces first and avoid widening scope into unrelated runtime behaviour.
- Staged migration, not big-bang replacement. Task 8 identifies hidden coupling between the current runtime, overlays, wrapper behaviour, and environment defaults. Those couplings should be removed in controlled stages rather than in one uncontrolled implementation.
- Explicit handling of backward incompatibility. Task 3 classifies logical `airflow` targeting and SQLite as legacy. Any implementation that removes them must do so as an intentional breaking change, not as silent compatibility behaviour.
- Overlay behaviour must converge to the canonical model. Task 1 and Task 8 show Community overlays are structurally close to the contract but still depend on `services.airflow` and packaged-versus-dev activation drift. The design must converge those behaviours on explicit base-runtime services.
- Runtime correctness precedes convenience. Task 8 classifies split Airflow services, PostgreSQL metadata, and removal of logical `airflow` dependency as blockers. Convenience paths that preserve legacy assumptions should not be treated as higher priority than contract correctness.

## 4. Alignment Strategy Overview

Community should align in four stages:

- Stage 1 establishes the canonical runtime foundation by removing the single-service Airflow model and SQLite dependency.
- Stage 2 aligns overlays to the explicit-service runtime so overlays no longer depend on a non-contract service surface.
- Stage 3 removes secrets and environment ambiguity so runtime configuration is explicit and placeholder-based.
- Stage 4 aligns validation so Community pass/fail conditions match the canonical runtime rather than the legacy Community runtime.

The design intent is to separate runtime-topology changes from overlay migration and from environment cleanup, while still preserving a strict execution order. Stage 1 must land before overlay alignment is considered complete, because overlays must target services that actually exist in the base runtime. Stage 4 is last because validation should measure the fully aligned target, not the transitional state.

## 5. Stage 1 — Runtime Foundation

Goal:
- Replace the legacy Community Airflow runtime shape with the canonical base-runtime topology and metadata model.

Scope:
- base Compose service topology for Airflow
- Airflow metadata backend stance
- high-level reset approach for legacy SQLite state
- dependency ordering between the Airflow database, Airflow init, and long-running Airflow services

What changes:
- Remove the logical `airflow` service from the Community base runtime.
- Introduce explicit long-running Airflow services:
  - `airflow-webserver`
  - `airflow-scheduler`
- Introduce a dedicated Airflow metadata database service for Community alignment:
  - `airflow-postgres`
- Retain an explicit one-shot Airflow initialization step as part of the Compose topology:
  - `airflow-user-init`
- Replace SQLite metadata assumptions with PostgreSQL-backed SQLAlchemy connection settings for all Airflow services.
- Replace the SQLite-oriented persistence model with a PostgreSQL data volume model.

Required services:
- `airflow-postgres` as the metadata database service
- `airflow-user-init` as the migration and admin-bootstrap step
- `airflow-webserver` as the Airflow UI/API service
- `airflow-scheduler` as the scheduling service

Community metadata stance:
- Community should align to PostgreSQL, not define a Community-specific SQLite exception.
- Reasoning:
  - Task 8 classifies SQLite removal as part of the required alignment scope.
  - Task 3 identifies PostgreSQL-backed Airflow metadata as the canonical direction.
  - A Community-specific SQLite stance would preserve the exact drift this task is intended to remove.

Migration/reset approach:
- Do not design a SQLite-to-PostgreSQL metadata migration path.
- Treat existing SQLite metadata as obsolete local runtime state and require reset during implementation.
- Remove reliance on the current SQLite-oriented volume and any repo-local `airflow.db` artifacts from the aligned runtime path.
- The implementation task should make the reset explicit so the break is deliberate and documented.

Compatibility considerations:
- This stage is intentionally backward-incompatible for local Airflow metadata state.
- This stage should not attempt to preserve a logical `airflow` compatibility alias, because the contract explicitly forbids that surface.
- Overlays should remain metadata-backend-agnostic; they should interact with Airflow through filesystem surfaces and explicit service targeting only.

Dependencies:
- Canonical contract direction from `overlay_contract_v1.md`
- Supported Compose Postgres design from Task 4 for naming, topology, and reset policy
- Existing Community overlay alignment work deferred to Stage 2

Risks:
- Local developer environments will lose prior SQLite metadata state.
- Any undocumented scripts or habits that assume one combined Airflow container will break.
- If Stage 1 is mixed with overlay rewrites in one implementation step, blast radius increases materially.

What must NOT be touched:
- overlay content
- overlay packaging archives
- DAG logic
- notebooks
- runtime documentation outside the implementation task scope
- any contract text

## 6. Stage 2 — Overlay Model Alignment

Goal:
- Make all Community overlays target only real services in the aligned base runtime and remove dependence on the legacy logical `airflow` abstraction.

Scope:
- overlay YAML targeting rules
- dev overlay files
- packaged overlay files
- behavioural treatment of overlays that still target `services.airflow`

What changes:
- Remove `services.airflow` from all Community overlay Compose files.
- Map Airflow-related overlay runtime configuration to:
  - `airflow-webserver`
  - `airflow-scheduler`
- Keep overlay integration filesystem-first wherever possible so only narrow explicit service overrides remain.
- Align packaged and dev overlay activation semantics so they express the same service model even if packaging mechanics remain different.

Overlay mapping model:
- Airflow environment variables or Airflow-visible mounts that must exist in both long-running Airflow services should be duplicated explicitly to both `airflow-webserver` and `airflow-scheduler`.
- Jupyter-only and PHP-only overrides should remain on their own existing services.
- Overlays should not introduce a new abstraction layer to avoid duplication, because the contract permits only explicit overrides against services that exist in the base runtime.

Handling existing overlays:
- Legacy overlays that still target `services.airflow` should fail validation after the migration rather than be adapted at runtime.
- Reasoning:
  - Task 8 identifies failure of invalid overlays as part of the canonical validation model.
  - Task 3 classifies logical `airflow` targeting as legacy to be removed.
  - A runtime compatibility shim would prolong non-canonical behaviour and hide required overlay changes.

Packaged versus dev consistency:
- Packaged and dev overlays must converge on the same runtime targeting model.
- The design does not require identical file layout between packaged and dev forms, but it does require identical service semantics.
- Any packaged overlay path that currently appears to work only because files are copied into base surfaces must still be treated as subject to the same explicit-service rules.

Duplication versus refactor strategy:
- Prefer controlled duplication of small Airflow override blocks across `airflow-webserver` and `airflow-scheduler`.
- Do not introduce a broader overlay refactor layer solely to avoid duplication.
- Reasoning:
  - minimal duplication is safer than inventing a new abstraction
  - the contract is explicit-service based, not alias-based
  - Task 3 warns against widening overlay service mutation beyond what is necessary

Dependencies:
- Stage 1 must complete first so overlays can target a stable canonical base runtime.

Risks:
- Overlay breakage is the main intentional breaking change in this stage.
- Packaged overlays with historical copy/unzip behaviour may be misread as exempt from explicit-service targeting unless implementation documents the rule clearly.
- Overlays that rely on inherited environment or image behaviour may surface hidden coupling once service targeting is corrected.

What must NOT be touched:
- base runtime topology decisions already defined by Stage 1
- overlay business logic
- overlay DAG contents
- notebooks and data artifacts
- any non-overlay runtime expansion

## 7. Stage 3 — Environment and Secrets

Goal:
- Replace implicit, repo-committed, and real-secret runtime behaviour with an explicit placeholder-based environment model aligned to the contract.

Scope:
- runtime secret handling policy
- required environment-variable inventory
- placeholder policy for committed examples
- removal of implicit environment assumptions relied on by overlays

What changes:
- Remove real credentials from the Community repo runtime path.
- Replace committed real values with placeholders or examples only.
- Define a required explicit environment model for the aligned Community runtime.
- Eliminate overlay/runtime behaviour that depends on undeclared inherited environment values.

Required environment-variable categories:
- Airflow Postgres variables:
  - `AIRFLOW_POSTGRES_USER`
  - `AIRFLOW_POSTGRES_PASSWORD`
  - `AIRFLOW_POSTGRES_DB`
- Airflow admin bootstrap variables:
  - `AIRFLOW_ADMIN_USERNAME`
  - `AIRFLOW_ADMIN_PASSWORD`
  - `AIRFLOW_ADMIN_EMAIL`
- existing object-storage variables required by the base runtime and overlays
- any overlay-required runtime variables that are currently implicit and therefore need to become explicit

Secrets model:
- Real credentials must not be committed.
- Example files may contain placeholders only.
- Runtime execution should supply secrets through local environment injection rather than versioned concrete values.

Implicit-env cleanup rules:
- Every variable required for successful base runtime startup must be explicitly named.
- Every variable required by an overlay at runtime must be explicitly documented as an overlay input, not assumed through incidental inheritance.
- Default demo credentials that remain as examples should be treated as placeholders, not as an endorsed persistent secret model.

Dependencies:
- Stage 1 establishes the new Airflow Postgres variable set.
- Stage 2 identifies which overlay assumptions still depend on inherited environment state.

Risks:
- Tightening the environment contract may expose undocumented local setup habits.
- Some overlays may appear to regress until their required variables are surfaced explicitly.
- If implementation mixes secrets cleanup with unrelated config redesign, scope can expand quickly.

What must NOT be touched:
- `.env` file contents in this design task
- overlay configs themselves in this design task
- secret storage systems outside the local runtime path
- contract wording

## 8. Stage 4 — Validation Model

Goal:
- Define canonical pass/fail checks for Community after alignment so validation reflects the new runtime contract rather than the old Community runtime.

Scope:
- startup validation
- Airflow service health validation
- overlay validity checks
- pass/fail criteria

What changes:
- Replace legacy validation assumptions with explicit aligned runtime checks.
- Treat invalid legacy overlay targeting as a validation failure, not as a tolerated compatibility case.

Required checks:
- Compose startup:
  - PASS if the aligned Compose stack starts with the expected Airflow-related services present and ordered correctly.
  - FAIL if startup still depends on a single logical `airflow` service or SQLite metadata.
- Airflow health:
  - PASS if `airflow-postgres` is healthy, `airflow-user-init` completes successfully, `airflow-webserver` is healthy, and `airflow-scheduler` remains running after initialization.
  - FAIL if migrations do not complete, the webserver is unhealthy, the scheduler exits, or metadata still points to SQLite.
- Overlay execution:
  - PASS if valid overlays start against explicit services and their filesystem content is visible through the canonical runtime surfaces.
  - FAIL if an overlay requires a logical `airflow` target or depends on a removed compatibility path.
- Failure of invalid overlays:
  - PASS if overlays that still reference `services.airflow` fail clearly and predictably.
  - FAIL if the runtime silently adapts invalid overlay definitions or preserves a logical `airflow` alias.

Definition of success:
- Community is compliant when:
  - base runtime exposes `airflow-postgres`, `airflow-user-init`, `airflow-webserver`, and `airflow-scheduler`
  - SQLite is no longer part of the runtime path
  - no active overlay targets logical `airflow`
  - secrets are placeholder-only in versioned examples
  - runtime and overlay inputs are explicit enough to remove hidden env coupling

Dependencies:
- Stages 1 through 3 must be implemented before validation can pass.

Risks:
- Validation may appear stricter than the historical Community workflow because it intentionally rejects legacy overlays and legacy metadata state.
- If implementation does not document failure expectations clearly, users may misread intentional failures as regressions rather than contract enforcement.

What must NOT be touched:
- no new runtime features beyond what is required to validate alignment
- no compatibility shims to make failing overlays appear valid

## 9. Risks and Breaking Changes

Primary breaking changes:
- local SQLite-backed Airflow state will be discarded
- any workflow that expects one logical `airflow` service will break
- overlays that still target `services.airflow` will stop working until migrated
- implicit environment assumptions will no longer be accepted as valid runtime configuration

User impact:
- local developers will need to reset Airflow metadata state
- overlay maintainers will need to update overlay Compose targeting
- users relying on repo-committed secrets or undeclared variables will need to move to explicit runtime injection

Rollback assumptions:
- rollback should be treated as source rollback, not metadata preservation
- once SQLite state is discarded and overlay targeting is migrated, the design assumes the project should not reintroduce the logical `airflow` surface as a fallback compatibility layer
- rollback, if required during implementation, should restore prior runtime files rather than attempting bidirectional metadata conversion

Top risks:
- implementation may try to combine Stage 1 and Stage 2 into one large change and increase failure scope
- packaged overlay semantics may hide legacy `airflow` assumptions that are easy to miss
- environment cleanup may surface more undocumented overlay inputs than Task 8 could prove from the limited input set
- local validation may be blocked by pre-existing repository state unrelated to Task 9
- downstream docs or helper scripts outside the allowed input set may still describe the legacy runtime shape

## 10. Implementation Sequencing

Recommended order:

1. Implement Stage 1 only:
   - split the base Airflow runtime
   - add Community PostgreSQL metadata service
   - remove SQLite runtime dependence
   - document reset expectations
2. Implement Stage 2:
   - migrate all Community overlays off `services.airflow`
   - align packaged and dev overlay targeting semantics
   - allow invalid legacy overlays to fail
3. Implement Stage 3:
   - remove committed real credentials
   - replace examples with placeholders
   - make required runtime and overlay env variables explicit
4. Implement Stage 4:
   - validate aligned Compose startup
   - validate Airflow service health
   - validate valid overlays
   - validate failure of invalid legacy overlays

Execution constraints:
- do not merge Stage 2 ahead of Stage 1
- do not hide Stage 2 breakage behind a compatibility shim
- do not defer secrets cleanup until after validation, because the environment model is part of contract compliance

## 11. Recommended Next Task

The next task should be Community implementation of Stage 1 only: replace the single logical `airflow` service with `airflow-postgres`, `airflow-user-init`, `airflow-webserver`, and `airflow-scheduler`, and remove SQLite from the Community runtime path without attempting overlay migration in the same task.

## 12. Validation Evidence

- Community repository verified at `/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community`
- Supported repository verified at `/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-supported`
- Both repositories verified on branch `feature/rearchitecture-runtime-overlay-contract`
- Inputs reviewed were limited to:
  - `docs/internal/task_1_community_runtime_overlay_discovery.md`
  - `docs/internal/task_8_community_supported_delta_analysis.md`
  - `docs/internal/task_3_runtime_comparison_and_canonical_findings.md`
  - `docs/internal/task_4_supported_compose_postgres_design.md`
  - `docs/architecture/overlay_contract_v1.md`
- No runtime, overlay, contract, Docker, Kubernetes, DAG, notebook, or config files were modified by this task
- Task 9 output is design documentation only
- Final repository-state validation is expected to remain blocked if pre-existing unrelated changes are still present in either repository
