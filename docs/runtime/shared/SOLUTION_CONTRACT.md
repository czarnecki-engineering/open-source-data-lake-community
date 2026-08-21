# Solution Contract

**Status: Confirmed** — This contract was validated without amendment through the complete five-stage `asx_ohlcv` solution pipeline (raw ingestion, conformed normalisation, curated aggregation, Iceberg materialisation, and Jupyter EDA notebook). No contract gap was discovered. The contract semantics generalise correctly from the heartbeat proving slice to a second real-data solution including all optional component types.

This contract does not add machinery. It records conventions already present in the heartbeat implementation so they can be followed consistently for future solutions.

---

## 1. What Is a Solution

A solution is a named, independently runnable Knowledge Lake workflow that:

- is identified by a slug
- spans at least one Airflow DAG and one PHP presentation page
- produces durable MinIO artifacts as its authoritative pipeline output
- can be re-run without depending on another solution's runtime state or Python modules

---

## 2. Slug Naming Convention

- Lowercase, underscore-separated: `heartbeat`, `asx_ohlcv`
- One slug per solution, used consistently across every component of that solution
- No hyphens, no uppercase, no camelCase
- The slug is the sole organising principle across all flat solution directories

---

## 3. Required Components

Every solution must include:

| Component | Path Pattern | Notes |
|---|---|---|
| PHP presentation page | `runtime/shared/php/solutions/{slug}.php` | Must include `Solution Title` and `Solution Summary` metadata comments near the top of the file |
| At least one Airflow DAG | `runtime/shared/dags/{slug}_*.py` | Slug-prefixed; one or more DAG files depending on pipeline stages |

---

## 4. Optional Components

A solution may also include:

| Component | Path Pattern | Notes |
|---|---|---|
| Config JSON | `runtime/shared/config/dags/{slug}.json` | Read-only source of truth for solution config; mounted into Airflow, Jupyter, and FrankenPHP at standard container config paths |
| DAG runtime helper | `runtime/shared/dags/{slug}_runtime.py` | Shared helper for the solution's own DAGs only; must not be imported by other solutions |
| Jupyter notebook | `runtime/shared/notebooks/{slug}_analysis.ipynb` | Subordinate analysis notebook; writes local summary artifact if FrankenPHP needs a summary signal |
| Local summary artifact | `runtime/shared/data/{slug}_summary.json` | Generated, untracked; written by the notebook, read by the PHP page |
| Solution Tag | `Solution Tag: {tag}` in PHP metadata comments | Optional tag for `ENABLED_SOLUTION_TAGS` gating through the solution discovery helper |

---

## 5. Authored vs Generated Assets

**Authored** (tracked in git):

- `runtime/shared/config/dags/{slug}.json`
- `runtime/shared/dags/{slug}_*.py` and optional `{slug}_runtime.py`
- `runtime/shared/notebooks/{slug}_analysis.ipynb`
- `runtime/shared/php/solutions/{slug}.php`

**Generated** (untracked, local runtime artifacts):

- `runtime/shared/data/{slug}_summary.json` — written by the notebook at runtime, not committed
- MinIO objects in `raw`, `conformed`, and `curated` buckets — produced by Airflow DAGs, not committed

---

## 6. Config Authority

- `runtime/shared/config/` is the canonical repo-visible config root for the current local runtime
- Per-solution config lives at `runtime/shared/config/dags/{slug}.json`
- Config is mounted read-only into containers at:
  - Airflow: `/opt/airflow/config`
  - Jupyter: `/home/jovyan/config`
  - FrankenPHP: `/app/config`
- No copied config files under DAG or notebook directories
- No symlink-based config workarounds

---

## 7. DAG Authority

- `runtime/shared/dags/` is the only authored DAG source for the current local runtime
- Solution DAG files follow slug-prefix naming: `{slug}_raw.py`, `{slug}_raw_to_conformed.py`, `{slug}_conformed_to_curated.py`, `{slug}_curated_to_iceberg.py` as applicable to the solution's pipeline stages
- The optional helper module is `{slug}_runtime.py` in the same directory
- No solution DAG files under other runtime paths

---

## 8. Artifact Authority

### Durable pipeline artifacts

- All durable pipeline outputs live in MinIO buckets: `raw`, `conformed`, `curated`
- New solutions use `{bucket}/{slug}/...` as their object root
  - example: `raw/asx_ohlcv/...`, `conformed/asx_ohlcv/...`, `curated/asx_ohlcv/...`
- The existing heartbeat solution uses `raw/reference/heartbeat/...` which predates this convention; do not normalize those paths
- MinIO objects are generated artifacts and are not tracked in git

### Local working artifacts

- `runtime/shared/data/` is the local working-files path for generated local summaries only
- The per-solution local summary at `data/{slug}_summary.json` is a local-only artifact that Jupyter writes and FrankenPHP reads
- `runtime/shared/data/` is not an alternative data lake, not a MinIO replacement, and not a persistence authority

---

## 9. Notebook Role

- Notebooks are subordinate analysis and consumption surfaces only
- A notebook may read MinIO artifacts directly using `boto3` through the container-local vendor path, or query Trino
- A notebook writes `runtime/shared/data/{slug}_summary.json` when FrankenPHP needs a local summary signal
- Notebooks do not own any MinIO zone, do not orchestrate DAGs, and do not mutate catalog state
- The current Jupyter `emptyDir`-backed vendor install for `boto3` is a provisional bridge, not a long-term dependency model

---

## 10. PHP Page Role

The PHP page at `runtime/shared/php/solutions/{slug}.php` is the human-visible presentation surface for the solution.

It is strictly read-only:

- it never triggers Airflow
- it never mutates MinIO
- it never queries Trino directly

It reads two optional local files only:

- `/app/config/dags/{slug}.json` — the mounted solution config (if a config file is present)
- `/app/data/{slug}_summary.json` — the notebook-written local summary (if a notebook is present)

It displays expected artifact paths as documentation strings, not live queries.

### Metadata comments

Every solution PHP page must include these metadata comments near the top of the file:

```php
/*
Solution Title: Human-Readable Title
Solution Summary: One sentence describing what this solution does.
*/
```

An optional `Solution Tag: {tag}` line controls tag-gated discovery through `ENABLED_SOLUTION_TAGS`.

### Two-tier checklist pattern

The PHP page uses two checklist sections:

- **Implementation checks** — static presence of authored source files (DAGs, config, notebook, PHP page). Always true once those files are authored; confirms the solution is wired up correctly.
- **Runtime checks** — dynamic presence of generated artifacts (the local summary JSON). Reflects whether the last DAG chain and notebook pass completed successfully.

---

## 11. Validation Semantics

A solution is **validated** when:

1. The Airflow DAG chain completes without error
2. The expected MinIO artifacts exist in the correct zones
3. The PHP page renders without PHP errors and shows expected paths
4. If a notebook is present: the notebook executes without error and writes `data/{slug}_summary.json`

Runtime validators (`validate-*.sh`) remain runtime-level: they validate startup, smoke, storage classes, search baseline, and config visibility. No per-solution `validate-{slug}.sh` scripts are added. The PHP two-tier checklist is the solution-specific validation surface.

---

## 12. Cross-Solution Independence

- Solutions must not import Python modules from each other
- A solution's `{slug}_runtime.py` helper is local to that solution only
- Data exchange between solutions, if ever needed, goes through MinIO object paths only
- Only future runtime-level shared utilities housed outside the solution slug namespace may be shared across solutions

---

## 13. Python Dependency Policy

### Platform and runtime dependencies

Python libraries that are broadly required across the Knowledge Lake runtime are pre-installed into the shared Airflow vendor path (`/opt/airflow/vendor`) by the `install-governed-dataset-dependencies` init container at pod startup.

Current platform-level examples:

- `boto3` — MinIO object access across the platform
- `pyiceberg` — Iceberg table materialisation across the platform

### Solution-specific dependencies

Libraries required only by a single solution are not automatically elevated to platform runtime image dependencies.

Current example: `yfinance` is required only by the `asx_ohlcv` solution and is not installed at pod startup.

### Accepted current operational pattern

Solution-specific Python libraries are installed dynamically into the existing shared vendor/emptyDir path during first task execution after pod startup. The `{slug}_runtime.py` helper is responsible for this install when the library is not already importable from the vendor path.

This is preferred over:

- `!pip install` cells inside Jupyter notebooks — **explicitly rejected** as a standard operational model; installs in notebook cells are not reproducible across sessions, are invisible to Airflow, and create uncontrolled divergence
- uncontrolled per-user installs
- premature solution-specific container image proliferation

### Rationale

- **Simplicity**: no new packaging infrastructure is required at current scale
- **Local-first alignment**: reuses the vendor/emptyDir bridge that already exists for platform dependencies
- **Avoids premature image proliferation**: separate container images per solution would increase local runtime complexity without benefit at current scale
- **Avoids notebook drift**: keeping installs in DAG runtime helpers rather than notebook cells keeps the operational surface consistent and inspectable

### Caveats and scope

- On first execution after each pod restart, the install adds latency to the first task run of that solution (emptyDir is cleared on restart)
- This is an intentionally simple local-first operational compromise, accepted because the current runtime is local-only
- It is **not** final enterprise packaging architecture and is subject to future refinement if operational complexity grows
- Premature custom image management or packaging framework design is intentionally deferred at current scale

---

## 14. Explicit Non-Goals

This contract does not define and does not permit:

- A metadata platform or catalog service
- A registry service or solution database
- A plugin model or extension framework
- A code generation or scaffolding framework
- A template engine
- Vector or RAG capability
- Cloud-production packaging or deployment automation
- Multi-tenant solution packaging
- Enterprise workflow orchestration above Airflow
- Per-solution `validate-{slug}.sh` scripts
- Any new runtime service
