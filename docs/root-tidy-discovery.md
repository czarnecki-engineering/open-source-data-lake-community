# Root Tidy Discovery

Note: this discovery report reflects the pre-move assessment state. Current locations are `docs/reference/CONTENTS.md`, `docs/reference/IMPLEMENTED_CAPABILITIES.md`, `docs/internal/PROJECT_CONTEXT.md`, and `docs/internal/TODO.md`.

## 1. Current root inventory

| item | classification | rationale |
| --- | --- | --- |
| `.DS_Store` | `UNKNOWN` | OS artefact, not part of repo structure, no repository value found. |
| `.env.example` | `WORKSPACE_HELPER` | Root env template for compose/operator use; referenced by docs and follows normal root convention. |
| `.gitignore` | `SHOULD_STAY_UNCHANGED` | Standard repo-root Git ignore file; controls ignored runtime artefacts such as `logs/` and `.env`. |
| `.gitignore copy` | `UNKNOWN` | Duplicate-looking helper/artifact, not referenced anywhere meaningful for runtime or docs. |
| `CONTENTS.md` | `CANDIDATE_TO_MOVE` | Root-level documentation index; docs-only, no runtime role. |
| `IMPLEMENTED_CAPABILITIES.md` | `CANDIDATE_TO_MOVE` | Evidence matrix / reference document; docs-only, no runtime role. |
| `PROJECT_CONTEXT.md` | `CANDIDATE_TO_MOVE` | Architecture/context summary; useful, but docs-only. |
| `README.md` | `OPERATOR_ENTRYPOINT` | Primary top-level orientation and quick-start. |
| `RUNBOOK.md` | `OPERATOR_ENTRYPOINT` | Canonical operational workflow linked directly from `README.md`. |
| `TODO.md` | `CANDIDATE_TO_MOVE` | Internal planning/documentation gap list; not a runtime or operator entrypoint. |
| `config/` | `RUNTIME_REQUIRED_AT_ROOT` | Bound into Airflow as `./config:/opt/airflow/config:ro` in `docker-compose.yaml:82`. |
| `dags/` | `RUNTIME_REQUIRED_AT_ROOT` | Bound into Airflow as `./dags:/opt/airflow/dags` in `docker-compose.yaml:79`. |
| `docker/` | `SHOULD_STAY_UNCHANGED` | Build context uses `docker/airflow/Dockerfile` and `docker/jupyter/Dockerfile` from root-relative paths in `docker-compose.yaml:42-45`, `99-101`. |
| `docker-compose.yaml` | `RUNTIME_REQUIRED_AT_ROOT` | Core runtime definition; scripts assume it is in the current root. |
| `docs/` | `DOC_REFERENCE` | Existing documentation home; safest consolidation target for docs-only files. |
| `logs/` | `RUNTIME_REQUIRED_AT_ROOT` | Bound into Airflow as `./logs:/opt/airflow/logs` in `docker-compose.yaml:80`. |
| `notebooks/` | `RUNTIME_REQUIRED_AT_ROOT` | Bound into Jupyter as `./notebooks:/home/jovyan/work` in `docker-compose.yaml:109`. |
| `open-source-data-lake-community.code-workspace` | `WORKSPACE_HELPER` | Editor helper; not used by runtime, but conventionally kept at root for IDE usability. |
| `php/` | `RUNTIME_REQUIRED_AT_ROOT` | Bound into PHP as `./php:/app/public` in `docker-compose.yaml:119`. |
| `plugins/` | `RUNTIME_REQUIRED_AT_ROOT` | Bound into Airflow as `./plugins:/opt/airflow/plugins` in `docker-compose.yaml:81`. |
| `start-compose.sh` | `OPERATOR_ENTRYPOINT` | Canonical startup wrapper; explicitly requires running from repo root and checks for `docker-compose.yaml` in CWD (`start-compose.sh:10-17`). |
| `stop-compose.sh` | `OPERATOR_ENTRYPOINT` | Canonical shutdown wrapper; explicitly requires `docker-compose.yaml` in CWD (`stop-compose.sh:28-30`). |

## 2. Path dependency findings

### Runtime-bound root items

- `docker-compose.yaml` must remain at root.
  Evidence: `start-compose.sh:15-17` and `stop-compose.sh:28-30` both check for a file literally named `docker-compose.yaml` in the current directory. `RUNBOOK.md:30-31` also defines the repo root as the folder containing `docker-compose.yaml`.
- `config/`, `dags/`, `logs/`, `plugins/`, `notebooks/`, and `php/` are exact relative bind mounts from the repo root.
  Evidence: `docker-compose.yaml:78-83`, `108-109`, `117-119`.
- `docker/` is root-relative build input.
  Evidence: `docker-compose.yaml:42-45` and `99-101` use `context: .` plus `dockerfile: docker/...`.

### Candidate docs: reference map

| item | referenced by scripts | referenced by `docker-compose.yaml` | referenced by docs | referenced by PHP/pages/notebooks/other repo files | exact relative path dependency | moving impact |
| --- | --- | --- | --- | --- | --- | --- |
| `CONTENTS.md` | No | No | `README.md:129`, `TODO.md:4` | None found outside docs/top-level docs | Yes, literal `CONTENTS.md` references in docs | Docs-only breakage |
| `IMPLEMENTED_CAPABILITIES.md` | No | No | `CONTENTS.md:7`, `docs/community-compose-alignment-execution.md:15` | None found from runtime files | Yes, literal filename in docs | Docs-only breakage |
| `PROJECT_CONTEXT.md` | No | No | `README.md:127`, `CONTENTS.md:4` | None found from runtime files | Yes, literal filename in docs | Docs-only breakage |
| `RUNBOOK.md` | No | No | `README.md:19`, `46`, `128`; `CONTENTS.md:6`; `PROJECT_CONTEXT.md:28`; `IMPLEMENTED_CAPABILITIES.md:10`; `TODO.md:5`, `17` | None from runtime code | Yes, literal filename in docs and user workflow text | Docs/operator breakage, not container runtime |
| `TODO.md` | No | No | `README.md:130`, `CONTENTS.md:8` | None found from runtime files | Yes, literal filename in docs | Docs-only breakage |
| `open-source-data-lake-community.code-workspace` | No | No | No repo references found | None | No internal dependency found | Likely safe technically, but root placement is the practical IDE convention |

### Other noteworthy root items

- `.env.example` is not consumed through `env_file:` in `docker-compose.yaml`, but it is explicitly referenced by documentation (`docs/community-compose-alignment-execution.md`) and is the normal operator-facing location for a compose env template.
- `.gitignore copy` and `.DS_Store` did not show meaningful dependency references. They are clutter signals, but not move targets.

## 3. Candidates for tidy-up

### 3.1 Safe to move

- `CONTENTS.md` -> `MOVE_TO_docs/reference`
  Reason: docs-only index; all impacts are doc link updates.
- `IMPLEMENTED_CAPABILITIES.md` -> `MOVE_TO_docs/reference`
  Reason: evidence/reference document; no runtime dependency found.
- `PROJECT_CONTEXT.md` -> `MOVE_TO_docs/internal`
  Reason: architecture/context note for maintainers; no runtime dependency found.
- `TODO.md` -> `MOVE_TO_docs/internal`
  Reason: internal planning document; only linked from other docs.

### 3.2 Safe only with path updates

- `RUNBOOK.md` -> possible `MOVE_TO_docs/reference`, but only with deliberate path updates.
  Evidence: `README.md` currently presents it as the canonical workflow (`README.md:19`, `46`), and multiple docs reference it by exact filename.
  Assessment: moving it would not break compose runtime, but it would reduce operator discoverability unless `README.md` is rewritten carefully.

### 3.3 Should stay at root

- `docker-compose.yaml`
- `start-compose.sh`
- `stop-compose.sh`
- `README.md`
- `config/`
- `dags/`
- `docker/`
- `logs/`
- `notebooks/`
- `php/`
- `plugins/`
- `.env.example`
- `open-source-data-lake-community.code-workspace` as `REMAIN_BUT_BE_DEEMPHASISED`

### Candidate-specific disposition requested in the brief

| item | disposition | evidence-based note |
| --- | --- | --- |
| `CONTENTS.md` | `MOVE_TO_docs/reference` | No runtime use; only doc links need updates. |
| `IMPLEMENTED_CAPABILITIES.md` | `MOVE_TO_docs/reference` | Reference material, not an entrypoint. |
| `PROJECT_CONTEXT.md` | `MOVE_TO_docs/internal` | Maintainer/context note rather than operator-first doc. |
| `RUNBOOK.md` | `STAY_AT_ROOT` | Strong operator-entrypoint role from `README.md`; moving is possible but not the minimal-risk option. |
| `TODO.md` | `MOVE_TO_docs/internal` | Internal planning artifact; docs-only dependency surface. |
| `open-source-data-lake-community.code-workspace` | `REMAIN_BUT_BE_DEEMPHASISED` | No repo dependency, but root placement is normal for IDE workspace files. |

## 4. Proposed target root layout

Minimal-disruption target:

```text
.
├── .env.example
├── README.md
├── RUNBOOK.md
├── docker-compose.yaml
├── start-compose.sh
├── stop-compose.sh
├── config/
├── dags/
├── docker/
├── docs/
│   ├── reference/
│   │   ├── CONTENTS.md
│   │   └── IMPLEMENTED_CAPABILITIES.md
│   └── internal/
│       ├── PROJECT_CONTEXT.md
│       └── TODO.md
├── logs/
├── notebooks/
├── php/
├── plugins/
└── open-source-data-lake-community.code-workspace
```

Notes:

- This keeps every proven root-relative runtime path unchanged.
- It avoids inventing a large new hierarchy; only `docs/reference` and `docs/internal` are added.
- `RUNBOOK.md` remains at root to preserve operator ergonomics.

## 5. Recommended minimal tidy-up plan

1. Leave the runtime layout untouched:
   `docker-compose.yaml`, `start-compose.sh`, `stop-compose.sh`, `docker/`, `config/`, `dags/`, `logs/`, `plugins/`, `notebooks/`, and `php/`.
2. Consolidate secondary documentation under `docs/`:
   move `CONTENTS.md`, `IMPLEMENTED_CAPABILITIES.md`, `PROJECT_CONTEXT.md`, and `TODO.md`.
3. Keep `README.md` and `RUNBOOK.md` at root:
   they are the two operator-facing entrypoints.
4. Keep `.env.example` at root:
   that is the expected compose/operator location even though it is not wired with `env_file:`.
5. Keep the workspace file if editor convenience matters, but do not treat it as part of the core root contract.
6. Separately review `.DS_Store` and `.gitignore copy` as cleanup artefacts.
   They are clutter, but this is not a move/restructure issue.

## 6. Risks

### SAFE NOW

- Moving `CONTENTS.md`, `IMPLEMENTED_CAPABILITIES.md`, `PROJECT_CONTEXT.md`, and `TODO.md` is safe from a runtime perspective.
- These files are not referenced by scripts, compose mounts, PHP runtime pages, or notebooks.

### SAFE WITH SMALL PATH UPDATES

- `CONTENTS.md`
  Update `README.md:129` and `TODO.md:4`.
- `IMPLEMENTED_CAPABILITIES.md`
  Update `CONTENTS.md:7` and `docs/community-compose-alignment-execution.md:15`.
- `PROJECT_CONTEXT.md`
  Update `README.md:127` and `CONTENTS.md:4`.
- `TODO.md`
  Update `README.md:130` and `CONTENTS.md:8`.
- `RUNBOOK.md` if moved
  Update `README.md:19`, `46`, `128`; `CONTENTS.md:6`; `PROJECT_CONTEXT.md:28`; `IMPLEMENTED_CAPABILITIES.md:10`; `TODO.md:5`, `17`.
  This is still docs/operator-only, but not the minimal-risk path.

### DO NOT TOUCH

- `docker-compose.yaml`
  Root move would break the wrapper scripts immediately and invalidate the root-relative compose convention.
- `start-compose.sh` and `stop-compose.sh`
  Their user-facing commands assume `./start-compose.sh` and `./stop-compose.sh` from root; moving them would force docs and workflow changes.
- `config/`, `dags/`, `logs/`, `plugins/`, `notebooks/`, `php/`
  Moving any of these would break exact bind mounts in `docker-compose.yaml`.
- `docker/`
  Moving it would require compose build path changes.
- `README.md`
  Moving it would hurt repo discoverability and standard GitHub landing behavior.

## 7. Appendix: references inspected

- `docker-compose.yaml`
- `start-compose.sh`
- `stop-compose.sh`
- `README.md`
- `RUNBOOK.md`
- `CONTENTS.md`
- `PROJECT_CONTEXT.md`
- `IMPLEMENTED_CAPABILITIES.md`
- `TODO.md`
- `.env.example`
- `.gitignore`
- `.gitignore copy`
- `open-source-data-lake-community.code-workspace`
- `config/README.md`
- `dags/README.md`
- `notebooks/README.md`
- `plugins/README.md`
- `php/index.php`
- `docs/community-mount-alignment-discovery.md`
- repository-wide `rg` searches for:
  `docker-compose.yaml`, `start-compose.sh`, `stop-compose.sh`, `README.md`, `RUNBOOK.md`, `CONTENTS.md`, `PROJECT_CONTEXT.md`, `IMPLEMENTED_CAPABILITIES.md`, `TODO.md`, `open-source-data-lake-community.code-workspace`, `config`, `dags`, `docker`, `docs`, `logs`, `notebooks`, `php`, `plugins`, `.env.example`
