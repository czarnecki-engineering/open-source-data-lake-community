# Open Source Data Lake Architecture

**Status:** implementation-backed architecture snapshot  
**Verified:** 14 September 2026  
**Scope:** Community, Foundation and Knowledge Lake local runtimes

## Authority and interpretation rules

This document describes capabilities that are implemented in the current repositories. It is deliberately derived from executable runtime artefacts, mounted code and supplied runtime data rather than from existing documentation.

For architecture purposes, evidence is ranked in this order:

1. runtime launchers and command-line profiles;
2. Docker Compose service definitions and their mounted paths;
3. active Kubernetes Kustomize overlays/profiles and the resources they select;
4. deployments/jobs/configuration actually selected by those runtimes;
5. code, DAGs, notebooks, PHP applications, scripts and data mounted into those selected runtimes.

Existing files under `docs/` are **not authoritative evidence** for a capability. They may be useful as navigation or historical context, but code, configuration and data win whenever they disagree with documentation.

A manifest or source file being present somewhere in a repository is not sufficient to call it a deployed feature. It must be reachable from the active runtime, or it must be an explicitly selectable add-on.

Legend used below:

- **✅ Default** — selected by the normal runtime path.
- **◐ Optional** — implemented and selected only by an explicit add-on/profile/runtime option.
- **— Absent** — not selected by the runtime and no explicit supported add-on path was identified.

## Repositories and runtime surfaces

The implementation currently exposes four distinct runtime surfaces across three repositories.

| Tier / variant | Repository | Authoritative runtime entry | Runtime content root |
|---|---|---|---|
| Community — Docker Compose | `czarnecki-engineering/open-source-data-lake-community` | `runtime/foundation/compose/docker-compose.yaml` | `runtime/shared/` |
| Foundation — Docker Compose | `czarnecki-engineering/open-source-data-lake-team` | `runtime/foundation/compose/docker-compose.yaml` | `runtime/shared/` |
| Foundation — Kubernetes | `czarnecki-engineering/open-source-data-lake-team` | `runtime/knowledge-lake/start-k8s.sh` → default `k8s/overlays/local`; `--full` → `k8s/overlays/local-full` | `runtime/shared/` |
| Knowledge Lake — Kubernetes | `czarnecki-engineering/open-source-knowledge-lake` | `runtime/knowledge-lake/start-k8s.sh` → `k8s/overlays/local` | `runtime/odl-mount/` |

The Foundation Kubernetes location is historically named `runtime/knowledge-lake/` in the Team repository. The active launcher and selected profiles, not the directory name, determine its tier identity.

## Runtime composition

### Community and Foundation Compose

Both Compose variants currently define the same principal runtime service set:

- MinIO object storage, with bootstrap creation of `raw`, `conformed` and `curated` buckets;
- PostgreSQL;
- Lakekeeper REST catalog;
- Trino;
- Apache Airflow initialization, webserver and scheduler;
- FrankenPHP;
- Jupyter;
- CloudBeaver.

The Compose runtime mounts the repository's `runtime/shared/` content into the appropriate services. Important bindings include:

- `runtime/shared/dags` → Airflow DAGs;
- `runtime/shared/scripts` → Airflow/Jupyter Python support code;
- `runtime/shared/notebooks` → Jupyter workspace;
- `runtime/shared/php` → FrankenPHP public application tree;
- `runtime/shared/trino` → Trino configuration/catalog files;
- `runtime/shared/data` → writable shared data workspace.

Evidence:

- Community: `runtime/foundation/compose/docker-compose.yaml`
- Foundation: `runtime/foundation/compose/docker-compose.yaml`

### Foundation Kubernetes

The Team repository's normal Kubernetes launcher is `runtime/knowledge-lake/start-k8s.sh`. Its default path is `runtime/knowledge-lake/k8s/overlays/local`, which selects `profiles/core`.

The default core profile selects:

- FrankenPHP;
- Jupyter;
- CloudBeaver;
- MinIO;
- PostgreSQL;
- Airflow;
- Lakekeeper;
- Trino.

The local overlay patches runtime mounts so Airflow and Jupyter consume `runtime/shared/` from the repository mount.

An explicit `--full` launcher option switches to `runtime/knowledge-lake/k8s/overlays/local-full`, which selects `profiles/full`. That profile adds:

- Metabase;
- Elasticsearch;
- Kibana;
- AI Access API;
- Open WebUI.

These five services are therefore optional Foundation Kubernetes capabilities, not default/core services.

Evidence:

- `runtime/knowledge-lake/start-k8s.sh`
- `runtime/knowledge-lake/k8s/overlays/local/kustomization.yaml`
- `runtime/knowledge-lake/k8s/profiles/core/kustomization.yaml`
- `runtime/knowledge-lake/k8s/overlays/local-full/kustomization.yaml`
- `runtime/knowledge-lake/k8s/profiles/full/kustomization.yaml`
- `runtime/knowledge-lake/k8s/overlays/local/airflow-scheduler-hostpath-patch.yaml`
- `runtime/knowledge-lake/k8s/overlays/local/jupyter-hostpath-patch.yaml`

### Knowledge Lake Kubernetes

The Knowledge Lake launcher uses one active local Kustomize path: `runtime/knowledge-lake/k8s/overlays/local`.

That overlay selects the complete Knowledge Lake base. The active base includes:

- CloudBeaver;
- FrankenPHP;
- Jupyter;
- MinIO;
- PostgreSQL;
- Airflow;
- Lakekeeper;
- Trino;
- Metabase;
- Elasticsearch;
- Kibana;
- AI Access API;
- Open WebUI.

The local patches mount `runtime/odl-mount/` content into the relevant pods, including DAGs, notebooks, PHP, Trino configuration, AI code and sample data.

Evidence:

- `runtime/knowledge-lake/start-k8s.sh`
- `runtime/knowledge-lake/k8s/overlays/local/kustomization.yaml`
- `runtime/knowledge-lake/k8s/base/kustomization.yaml`
- `runtime/knowledge-lake/k8s/overlays/local/airflow-scheduler-hostpath-patch.yaml`
- `runtime/knowledge-lake/k8s/overlays/local/jupyter-hostpath-patch.yaml`
- `runtime/knowledge-lake/k8s/overlays/local/ai-access-api-hostpath-patch.yaml`

## Capability matrix

| Capability | Community (Compose) | Foundation (Compose) | Foundation (Kubernetes) | Knowledge Lake (Kubernetes) | Implementation evidence |
|---|:---:|:---:|:---:|:---:|---|
| **Platform services** ||||||
| MinIO S3-compatible object storage | ✅ | ✅ | ✅ | ✅ | C/F Compose `docker-compose.yaml → services.minio`; Team K8s `profiles/core → base/minio`; Knowledge `base/kustomization.yaml → minio` |
| Raw / conformed / curated object zones | ✅ | ✅ | ✅ | ✅ | Compose `services.minio-init`; K8s MinIO bootstrap plus active DAGs targeting these buckets |
| PostgreSQL relational database | ✅ | ✅ | ✅ | ✅ | Compose `services.postgres`; Team core `base/postgres`; Knowledge base `postgres` |
| Lakekeeper Iceberg REST catalog | ✅ | ✅ | ✅ | ✅ | Compose `services.lakekeeper`; Team core `base/lakekeeper`; Knowledge base `lakekeeper` |
| Trino SQL query engine | ✅ | ✅ | ✅ | ✅ | Compose `services.trino`; Team core `base/trino`; Knowledge base `trino` |
| Trino PostgreSQL federation configuration | ✅ | ✅ | ✅ | ✅ | C/F `runtime/shared/trino/postgres.properties`; Team/Knowledge active Trino mounts |
| Apache Airflow orchestration | ✅ | ✅ | ✅ | ✅ | Compose `airflow-init`, `airflow-web`, `airflow-scheduler`; Team core Airflow resources; Knowledge `base/airflow` |
| FrankenPHP web/application runtime | ✅ | ✅ | ✅ | ✅ | Compose `services.frankenphp`; Team core imports Foundation FrankenPHP base; Knowledge base imports Foundation FrankenPHP base |
| Jupyter notebook runtime | ✅ | ✅ | ✅ | ✅ | Compose `services.jupyter`; Team core Jupyter; Knowledge base Jupyter |
| CloudBeaver browser SQL/database utility | ✅ | ✅ | ✅ | ✅ | Compose `services.cloudbeaver`; Team core CloudBeaver; Knowledge base CloudBeaver |
| Metabase BI / analytics | — | — | ◐ | ✅ | Team `profiles/full → addons/metabase`; Knowledge `base/kustomization.yaml → metabase` |
| Elasticsearch search engine | — | — | ◐ | ✅ | Team `profiles/full → addons/elasticsearch`; Knowledge base `elasticsearch` |
| Kibana search/inspection UI | — | — | ◐ | ✅ | Team `profiles/full → addons/kibana`; Knowledge base `kibana` |
| Deterministic AI Access API over Trino | — | — | ◐ | ✅ | Team `profiles/full → addons/ai-access-api` + `runtime/shared/ai/api/server.py`; Knowledge base `ai-access-api` + `runtime/odl-mount/ai/api/server.py` |
| Open WebUI conversational front end | — | — | ◐ | ✅ | Team `profiles/full → addons/open-webui`; Knowledge base `open-webui` |
| **Data pipelines and governed-data capabilities** ||||||
| ASX OHLCV raw ingestion | ✅ | ✅ | ✅ | ✅ | C/F/Team K8s `runtime/shared/dags/asx_ohlcv_raw.py`; Knowledge `runtime/odl-mount/dags/asx_ohlcv_raw.py` |
| ASX OHLCV raw → conformed | ✅ | ✅ | ✅ | ✅ | `asx_ohlcv_raw_to_conformed.py` in each active DAG mount |
| ASX OHLCV conformed → curated | ✅ | ✅ | ✅ | ✅ | `asx_ohlcv_conformed_to_curated.py` in each active DAG mount |
| ASX OHLCV curated → Iceberg | ✅ | ✅ | ✅ | ✅ | `asx_ohlcv_curated_to_iceberg.py` in each active DAG mount |
| Shared ASX OHLCV staged-pipeline runtime | ✅ | ✅ | ✅ | ✅ | C/F `runtime/shared/dags/asx_ohlcv_runtime.py`; Knowledge `runtime/odl-mount/dags/asx_ohlcv_runtime.py` |
| ASX sector-map curated pipeline | ✅ | ✅ | ✅ | — | C/F/Team K8s `runtime/shared/dags/asx_sector_map_curated.py`, `asx_sector_map_runtime.py`; no equivalent in active Knowledge DAG mount |
| Heartbeat raw → conformed → curated → Iceberg reference pipeline | ✅ | ✅ | ✅ | ✅ | `heartbeat_raw.py`, `heartbeat_raw_to_conformed.py`, `heartbeat_conformed_to_curated.py`, `heartbeat_curated_to_iceberg.py`, `heartbeat_runtime.py` in active DAG mounts |
| Governed customer CSV → Iceberg/Lakekeeper workflow | — | — | — | ✅ | Knowledge `runtime/odl-mount/dags/governed_customer_sample.py` |
| Structured / semi-structured / unstructured reference-asset publication | — | — | — | ✅ | Knowledge `runtime/odl-mount/dags/storage_class_baseline_assets.py` + `runtime/odl-mount/sample-data/` |
| Elasticsearch indexing of reference assets | — | — | — | ✅ | Knowledge `runtime/odl-mount/dags/search_baseline_index_assets.py` |
| Lakekeeper/Iceberg catalog probe DAG | — | — | — | ✅ | Knowledge `runtime/odl-mount/dags/iceberg_catalog_probe.py` |
| PostgreSQL customer-tier reference dataset | — | — | ✅ | ✅ | Team `runtime/knowledge-lake/k8s/base/postgres/reference-data-*`; Knowledge `runtime/knowledge-lake/k8s/base/postgres/reference-data-*` |
| **Application solutions** ||||||
| ASX OHLCV PHP solution | ✅ | ✅ | ✅ | ✅ | C/F `runtime/shared/php/solutions/asx_ohlcv.php`; Knowledge `runtime/odl-mount/php/solutions/asx_ohlcv.php` |
| Heartbeat PHP solution | ✅ | ✅ | ✅ | ✅ | C/F `runtime/shared/php/solutions/heartbeat.php`; Knowledge `runtime/odl-mount/php/solutions/heartbeat.php` |
| Runtime diagnostics PHP solution | ✅ | ✅ | ✅ | ✅ | C/F `runtime/shared/php/solutions/runtime_diagnostics.php`; Knowledge `runtime/odl-mount/php/solutions/runtime_diagnostics.php` |
| Kubernetes cluster-information PHP solution | — | — | — | ✅ | Knowledge `runtime/odl-mount/php/solutions/cluster_info.php` |
| **Analytical and developer capabilities** ||||||
| ASX analytical/research notebook | ✅ | ✅ | ✅ | ✅ | Community/Foundation `runtime/shared/notebooks/asx_publication_research.ipynb`; Knowledge `runtime/odl-mount/notebooks/asx_ohlcv_analysis.ipynb` |
| Heartbeat analysis notebook | ✅ | ✅ | ✅ | ✅ | C/F `runtime/shared/notebooks/heartbeat_analysis.ipynb`; Knowledge `runtime/odl-mount/notebooks/heartbeat_analysis.ipynb` |
| ASX local OHLCV acquisition / research tooling | ✅ | ✅ | ✅ | — | `runtime/shared/scripts/asx200_ohlcv_local.py`, `asx_research_panel.py`; Team K8s active Jupyter/Airflow mounts include `runtime/shared/scripts` |
| RBA cash-rate and STW benchmark tooling | ✅ | ✅ | ✅ | — | `runtime/shared/scripts/rba_cash_rate_tri_local.py`, `stw_benchmark_local.py` |
| Quantitative strategy/backtesting toolkit | ✅ | ✅ | ✅ | — | `runtime/shared/scripts/strategies/` including backtest, mean-reversion, pairs, walk-forward, cost and inference modules |
| Deterministic ASX natural-language query capability | — | — | ◐ | ✅ | Team `runtime/shared/ai/asx_ohlcv_ai_access.py`; Knowledge `runtime/odl-mount/ai/asx_ohlcv_ai_access.py` |
| OpenAI-compatible ASX chat API surface | — | — | ◐ | ✅ | Team/Knowledge `ai/api/server.py` implements `/v1/models` and `/v1/chat/completions` |
| Supplied customer sample data for governed/search demonstrations | — | — | — | ✅ | Knowledge `runtime/odl-mount/sample-data/customer_sample.csv`, `customer_events.jsonl`, `customer_notes.txt` |

Repository shorthand in the evidence column: **C** = Community repository; **F/Team** = Foundation Team repository; **Knowledge** = Knowledge Lake repository.

## Data and query architecture

Across the tiers, the implemented data-lake path is centered on MinIO object storage, Airflow orchestration, Lakekeeper catalog services and Trino query access.

The staged ASX and heartbeat DAG families implement the principal raw → conformed → curated progression and publication to Iceberg where the corresponding DAG is present in the active mount.

Trino is configured with both the Iceberg/Lakekeeper path and a PostgreSQL catalog configuration. In Foundation Kubernetes and Knowledge Lake, PostgreSQL also has a small runtime-seeded reference dataset (`reference.customer_tier_labels`).

Knowledge Lake adds standing reference workflows that exercise more data classes and access modes:

- `governed_customer_sample.py` materializes a governed sample into Lakekeeper/Iceberg;
- `storage_class_baseline_assets.py` publishes semi-structured JSONL and unstructured text assets to MinIO and writes a manifest;
- `search_baseline_index_assets.py` reads those assets and indexes them into Elasticsearch.

These are implementation features, not inferred target architecture.

## AI and search architecture

The Knowledge Lake AI access path is deliberately deterministic rather than a general-purpose RAG or autonomous SQL-generation layer.

`runtime/odl-mount/ai/api/server.py` exposes:

- `GET /health`;
- `GET /v1/models`;
- `POST /ask`;
- `POST /v1/chat/completions`.

Recognised questions are mapped to pre-written allowlisted SQL and executed through Trino. Open WebUI is configured to use the AI Access API's OpenAI-compatible endpoint.

The Team/Foundation implementation contains the same capability as an optional full-profile add-on under `runtime/shared/ai/`.

### Ollama exclusion

Ollama artefacts exist in the Knowledge Lake repository and the AI code can attempt optional Ollama-based wording when an Ollama endpoint is available. However, the active Knowledge Lake `runtime/knowledge-lake/k8s/base/kustomization.yaml` does **not** select the `ollama` base resource. Ollama is therefore not classified as a deployed Knowledge Lake feature in this document.

The same rule applies generally: artefact presence does not equal runtime capability.

## Tier progression

### Community → Foundation Compose

At the current implementation snapshot, Community Compose and Foundation Compose have substantially the same deployed service classes and mounted solution families. Foundation Compose should therefore not be described as a materially larger platform solely on the basis of tier naming.

### Foundation Compose → Foundation Kubernetes

The principal change is the operational runtime: Kubernetes becomes the deployment substrate while preserving the Foundation data, web, notebook and pipeline capabilities through repository mounts.

Foundation Kubernetes also includes runtime-seeded PostgreSQL reference data. Its explicit `--full` path adds Metabase, Elasticsearch, Kibana, AI Access API and Open WebUI, but these remain optional rather than default/core.

### Foundation Kubernetes → Knowledge Lake Kubernetes

Knowledge Lake promotes the search, BI and AI-access surfaces into its default selected runtime and adds active knowledge-oriented workflows: governed Iceberg sample data, multiple storage-class reference assets, Elasticsearch indexing, deterministic ASX query access and the Open WebUI conversational surface.

Knowledge Lake does not simply add services; it includes runtime artefacts that exercise those services together.

## Architecture review protocol

This file should be revalidated whenever runtime selection, mounted content, service composition or supplied solution code changes. A useful review uses four independent perspectives.

### 1. Runtime / platform reviewer

Verify only what is actually launched.

Checklist:

- trace launchers and command-line flags;
- for Compose, enumerate `services` and follow every bind mount/build reference that carries functionality;
- for Kubernetes, start from the launcher-selected overlay/profile and recursively trace Kustomize `resources`;
- distinguish default resources from add-ons and dormant manifests;
- do not infer deployment from filenames or directory names.

### 2. Data-engineering reviewer

Verify implemented data behaviour.

Checklist:

- inspect Airflow-mounted DAG directories;
- group wrapper DAGs with their substantial shared runtime modules rather than counting implementation files as separate features;
- identify external ingestion, transformations, persistence layers and Iceberg/catalog interactions;
- confirm sample/reference datasets are actually read by active jobs or applications;
- verify query/catalog connectors from runtime configuration.

### 3. Application / analytics / AI reviewer

Verify user-facing and developer-facing solutions.

Checklist:

- inspect FrankenPHP-mounted application code;
- inspect Jupyter-mounted notebooks and mounted analytical libraries/scripts;
- inspect optional and default UI services separately;
- for AI/search claims, verify the actual request/query path and avoid describing capabilities such as RAG, embeddings or free-form SQL unless the implementation contains them.

### 4. Evidence / adversarial reviewer

Attempt to disprove every capability claim.

For each row in the capability matrix ask:

1. What exact launcher or selected runtime makes this reachable?
2. What exact file/resource implements it?
3. Is it default, optional, merely present, or absent?
4. Does a mounted path actually contain the claimed solution?
5. Is the claim stronger than the implementation evidence?

If a claim cannot survive this review, remove or weaken it rather than filling the gap from existing documentation or intended architecture.

## Documentation maintenance rule

This architecture file is intended to survive a later documentation cleanup because its claims are tied directly to implementation back-references.

If other documentation conflicts with this file, do not automatically prefer this file either. Re-check the current code, configuration and data. The runtime implementation remains the ultimate authority.

When this document is updated, reviewers should record new or changed back-references rather than relying on prose inherited from older architecture documents.
