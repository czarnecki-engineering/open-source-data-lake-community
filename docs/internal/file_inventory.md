# File Inventory

Update prompt: when repository files are added, removed, renamed, or materially repurposed,
update the table below so each tracked file still has an accurate one-line description.

This inventory summarises the current tracked files in the repository as of June 4, 2026.

| File Path | Short Description |
| --- | --- |
| **Repository Root** |  |
| `.env.example` | Example environment file defining local runtime ports, credentials, and overlay toggles for the base Community stack. |
| `.gitignore` | Git ignore rules excluding runtime state, secrets, Python cache files, and notebook checkpoints from the repository. |
| `README.md` | Primary orientation document describing the Community edition, its scope, and the canonical docs to read first. |
| `RUNBOOK.md` | Operational runbook for starting, stopping, resetting, validating, and troubleshooting the base local Docker Compose runtime. |
| `docker-compose.yaml` | Authoritative base Compose manifest for MinIO, Airflow, Jupyter, and PHP services in the Community runtime. |
| `open-source-data-lake-community.code-workspace` | VS Code workspace manifest that opens the repository root with no extra editor settings. |
| `overlay_asx_historic_csv_v1.0.zip` | Tracked distributable zip archive containing the packaged ASX historic overlay payload; derived build artifact. |
| `overlay_file_only_demo_v1.0.zip` | Tracked distributable zip archive for the file-only demo overlay; derived build artifact. |
| `overlay_heartbeat_v2.zip` | Tracked distributable zip archive for the heartbeat v2 overlay; derived build artifact. |
| `overlay_hello_world_v1.0.zip` | Tracked distributable zip archive containing the packaged hello-world overlay payload; derived build artifact. |
| `overlay_kaggle_ingestion_v1.0.zip` | Tracked distributable zip archive containing the packaged Kaggle ingestion overlay payload; derived build artifact. |
| `start-compose.sh` | Authoritative base startup wrapper that validates `.env`, resolves overlay compose files, and launches the selected Docker Compose stack. |
| `stop-compose.sh` | Base shutdown wrapper that resolves overlay compose files and stops the selected Docker Compose stack, optionally removing volumes. |
| **config/** |  |
| `config/README.md` | Config note explaining that `config/asx200_tickers.csv` is local-only and that tracked samples seed the ASX DAGs. |
| `config/asx200_tickers_top100.csv` | Sample CSV containing roughly the top 100 ASX200 tickers for local ASX OHLCV pipeline configuration. |
| `config/asx200_tickers_top3.csv` | Minimal sample CSV containing three ASX tickers for quick-start ASX OHLCV pipeline tests. |
| **dags/** |  |
| `dags/asx200_ohlcv_backfill_to_raw.py` | Airflow DAG that backfills five years of ASX OHLCV raw data from Yahoo Finance with resumable state and audit artifacts. |
| `dags/asx200_ohlcv_conformed_to_curated_snapshot_v2.py` | Airflow DAG that compacts conformed ASX parquet partitions into one curated daily snapshot parquet per trade date. |
| `dags/asx200_ohlcv_daily_to_raw.py` | Airflow DAG that reads configured ASX tickers and lands daily Yahoo Finance OHLCV CSVs into the raw bucket. |
| `dags/asx200_ohlcv_raw_to_conformed_parquet.py` | Airflow DAG that standardizes raw ASX CSV objects into conformed parquet files with deterministic row hashes. |
| `dags/dag_heartbeat_v2_copy_conformed_to_curated.py` | Airflow DAG that copies new `heartbeat_v2/` objects from conformed to curated every minute. |
| `dags/dag_heartbeat_v2_copy_raw_to_conformed.py` | Airflow DAG that copies new `heartbeat_v2/` objects from raw to conformed every minute. |
| `dags/dag_heartbeat_v2_to_raw.py` | Airflow DAG that writes one timestamp file per minute into `raw/heartbeat_v2/` as the overlay heartbeat source step. |
| `dags/heartbeat_1m_copy_conformed_to_curated.py` | Base heartbeat Airflow DAG that copies new `heartbeat/` objects from conformed to curated every minute. |
| `dags/heartbeat_1m_copy_raw_to_conformed.py` | Base heartbeat Airflow DAG that copies new `heartbeat/` objects from raw to conformed every minute. |
| `dags/heartbeat_1m_to_raw.py` | Base heartbeat Airflow DAG that writes one timestamp file per minute into `raw/heartbeat/`. |
| **docker/** |  |
| `docker/airflow/Dockerfile` | Base Airflow image extension that installs the Python packages required by the tracked DAGs and notebooks. |
| `docker/jupyter/Dockerfile` | Base Jupyter image extension that installs data-analysis and MinIO client dependencies for local notebooks. |
| **docs/** |  |
| `docs/HOWTO_OVERLAYS.md` | Workflow guide for building, packaging, installing, and validating overlays against the repository's overlay contract. |
| `docs/architecture/overlay_contract_v1.md` | Authoritative overlay contract specification defining the filesystem surfaces and packaging rules overlays must follow. |
| `docs/releases/v1.1.0-overlay-contract-validation-and-installed-mode-stabilisation.md` | Release note recording the validated v1.1.0 overlay-contract consolidation and cross-repo installed-mode results. |
| `docs/standards/RUNBOOK_template.md` | Canonical runbook template for writing operational docs across runtime variants and overlays. |
| **notebooks/** |  |
| `notebooks/01_asx_eda.ipynb` | Jupyter notebook for exploratory analysis of curated ASX daily OHLCV data before any transforming decisions. |
| `notebooks/02_asx_preprocessing.ipynb` | Jupyter notebook that applies explicit preprocessing steps to ASX OHLCV data after the EDA stage. |
| `notebooks/heartbeat_v2_validation.ipynb` | Validation notebook that reads the latest `raw/heartbeat_v2/` object and prints its payload. |
| `notebooks/hello_world.ipynb` | Minimal notebook that prints `Hello World!`, retained as the smallest Jupyter sanity check. |
| `notebooks/read_heartbeat.ipynb` | Ad hoc validation notebook that lists heartbeat objects in MinIO and inspects the latest landed file. |
| `notebooks/read_ohlcv_daily.ipynb` | Inspection notebook that loads curated ASX parquet objects from MinIO and profiles memory and schema. |
| **overlay_asx_historic_csv/** |  |
| `overlay_asx_historic_csv/.env.example` | Example overlay env fragment documenting optional ASX historic bucket overrides and shared credentials. |
| `overlay_asx_historic_csv/config/asx_historic_jobs.example.json` | Example job manifest defining URL-driven ASX historic ingestion inputs and raw/conformed/curated targets. |
| `overlay_asx_historic_csv/dags/dag_asx_historic_csv.py` | Thin Airflow DAG wrapper that runs the ASX historic raw, conformed, and curated scripts in sequence. |
| `overlay_asx_historic_csv/dev-docker-compose.overlay-asx-historic-csv.yaml` | Development overlay Compose layer that mounts the ASX historic DAG, shared scripts, data mirror, and tagged PHP solution. |
| `overlay_asx_historic_csv/dev-start-compose.sh` | Dev wrapper that starts the base stack with the ASX historic development overlay compose file attached. |
| `overlay_asx_historic_csv/dev-stop-compose.sh` | Dev wrapper that stops the base stack with the ASX historic development overlay compose file attached. |
| `overlay_asx_historic_csv/docs/explanation.md` | Architecture note describing this overlay's HTTP tabular ingestion flow, output model, and PHP solution-tag contract. |
| `overlay_asx_historic_csv/docs/overlay_asx_historic_csv.md` | Compatibility doc retained only to point readers at the overlay's real explanation document. |
| `overlay_asx_historic_csv/notebooks/asx_historic_connectivity_and_eda.ipynb` | Validation notebook that checks source URL reachability, MinIO artifacts, and light EDA for the ASX historic overlay. |
| `overlay_asx_historic_csv/overlay_asx_historic_csv/README.md` | Packaged overlay README describing installed-mode contents, config contract, and archive layout for `overlay_asx_historic_csv_v1.0`. |
| `overlay_asx_historic_csv/overlay_asx_historic_csv/RUNBOOK.md` | Packaged runbook documenting the validated zip-build, unzip, configuration, and startup path for this overlay. |
| `overlay_asx_historic_csv/overlay_asx_historic_csv/docker-compose.overlay-asx-historic-csv.yaml` | Packaged installed-mode Compose layer that adds ASX historic dependencies, mounts, and PHP solution tagging. |
| `overlay_asx_historic_csv/overlay_asx_historic_csv/docker/airflow/Dockerfile` | Packaged Airflow image extension for this overlay, adding tabular ingestion dependencies including Excel readers. |
| `overlay_asx_historic_csv/overlay_asx_historic_csv/docker/jupyter/Dockerfile` | Packaged Jupyter image extension for ASX historic validation notebooks and tabular analysis tooling. |
| `overlay_asx_historic_csv/overlay_asx_historic_csv/start-compose.sh` | Packaged start wrapper that launches the installed overlay through its packaged compose file. |
| `overlay_asx_historic_csv/overlay_asx_historic_csv/stop-compose.sh` | Packaged stop wrapper that shuts down the installed overlay through its packaged compose file. |
| `overlay_asx_historic_csv/php/solutions/asx_historic_summary.php` | PHP solution page that renders curated ASX historic summary JSON mirrored under `data/curated/asx/historic`. |
| `overlay_asx_historic_csv/scripts/asx_overlay_common.py` | Shared helper library for the ASX historic overlay, covering config loading, MinIO access, path normalization, and local mirrors. |
| `overlay_asx_historic_csv/scripts/asx_urls_to_raw.py` | CLI ingestion script that downloads configured HTTP tabular files and uploads them into the raw MinIO bucket. |
| `overlay_asx_historic_csv/scripts/conformed_to_curated.py` | CLI curation script that summarizes conformed ASX parquet data into curated JSON and mirrors it locally for PHP. |
| `overlay_asx_historic_csv/scripts/raw_to_conformed.py` | CLI transform script that standardizes raw CSV/XLS/XLSX objects into conformed parquet outputs for this overlay. |
| **overlay_contract/** |  |
| `overlay_contract/README.md` | Compatibility README marking `overlay_contract/` as deprecated and redirecting readers to the authoritative docs paths. |
| **overlay_file_only_demo/** |  |
| `overlay_file_only_demo/dev-docker-compose.overlay-file-only-demo.yaml` | Minimal dev compose layer that only mounts the file-only demo solution into the PHP container. |
| `overlay_file_only_demo/dev-start-compose.sh` | Dev wrapper that starts the base stack with the file-only demo PHP overlay attached. |
| `overlay_file_only_demo/dev-stop-compose.sh` | Dev wrapper that stops the base stack with the file-only demo PHP overlay attached. |
| `overlay_file_only_demo/overlay_file_only_demo/README.md` | Packaged README for the minimal file-only overlay, emphasising that it needs no compose file or wrapper scripts. |
| `overlay_file_only_demo/overlay_file_only_demo/RUNBOOK.md` | Packaged runbook for the file-only demo overlay, covering zip build, unzip install, and validation through Solutions. |
| `overlay_file_only_demo/php/solutions/file_only_demo.php` | Minimal PHP solution page proving an additive overlay can work by shipping only a single solution file. |
| **overlay_heartbeat_v2/** |  |
| `overlay_heartbeat_v2/README.md` | Compatibility README retained only to redirect readers to the packaged heartbeat v2 docs. |
| `overlay_heartbeat_v2/RUNBOOK.md` | Compatibility runbook retained only to redirect readers to the packaged heartbeat v2 docs. |
| `overlay_heartbeat_v2/dags/dag_heartbeat_v2_copy_conformed_to_curated.py` | Overlay Airflow DAG that copies new `heartbeat_v2/` objects from conformed to curated every minute. |
| `overlay_heartbeat_v2/dags/dag_heartbeat_v2_copy_raw_to_conformed.py` | Overlay Airflow DAG that copies new `heartbeat_v2/` objects from raw to conformed every minute. |
| `overlay_heartbeat_v2/dags/dag_heartbeat_v2_to_raw.py` | Overlay Airflow DAG that writes one timestamp file per minute into `raw/heartbeat_v2/`. |
| `overlay_heartbeat_v2/dev-docker-compose.overlay-heartbeat-v2.yaml` | Development compose layer that mounts the overlay's DAGs into Airflow and its validation notebook into Jupyter. |
| `overlay_heartbeat_v2/dev-start-compose.sh` | Dev wrapper that starts the base stack with the heartbeat v2 development overlay attached. |
| `overlay_heartbeat_v2/dev-stop-compose.sh` | Dev wrapper that stops the base stack with the heartbeat v2 development overlay attached. |
| `overlay_heartbeat_v2/notebooks/heartbeat_v2_validation.ipynb` | Overlay validation notebook that reads the latest `raw/heartbeat_v2/` object and prints its payload. |
| `overlay_heartbeat_v2/overlay_heartbeat_v2/README.md` | Packaged README describing the heartbeat v2 overlay as a coexistence-safe copy of the base heartbeat workflow. |
| `overlay_heartbeat_v2/overlay_heartbeat_v2/RUNBOOK.md` | Packaged runbook covering dev mode, archive build, install, and validation for heartbeat v2. |
| `overlay_heartbeat_v2/overlay_heartbeat_v2/start-compose.sh` | Packaged start wrapper for the installed heartbeat v2 overlay; it delegates to the base start script. |
| `overlay_heartbeat_v2/overlay_heartbeat_v2/stop-compose.sh` | Packaged stop wrapper for the installed heartbeat v2 overlay; it delegates to the base stop script. |
| `overlay_heartbeat_v2/start-compose.sh` | Source-tree compatibility start wrapper for installed heartbeat v2 payloads; delegates to the base start script. |
| `overlay_heartbeat_v2/stop-compose.sh` | Source-tree compatibility stop wrapper for installed heartbeat v2 payloads; delegates to the base stop script. |
| **overlay_hello_world/** |  |
| `overlay_hello_world/config/hello_world_job.example.json` | Example job config defining deterministic hello-world input and output locations for the reference overlay. |
| `overlay_hello_world/dags/dag_hello_world.py` | Thin Airflow DAG that executes the hello-world local-to-raw, raw-to-conformed, and conformed-to-curated scripts in order. |
| `overlay_hello_world/data/sample/hello_world/hello_world_input.json` | Deterministic sample dataset that acts as the authoritative hello-world source payload. |
| `overlay_hello_world/dev-docker-compose.overlay-hello-world.yaml` | Development compose layer that mounts the hello-world overlay surfaces and enables its tagged PHP solution. |
| `overlay_hello_world/dev-start-compose.sh` | Dev wrapper that starts the base stack with the hello-world development overlay attached. |
| `overlay_hello_world/dev-stop-compose.sh` | Dev wrapper that stops the base stack with the hello-world development overlay attached. |
| `overlay_hello_world/docs/explanation.md` | Architecture note explaining the hello-world overlay's deterministic pipeline and its dev-mode mount behavior. |
| `overlay_hello_world/notebooks/hello_world_validation.ipynb` | Validation notebook that checks the curated hello-world summary against deterministic expected values. |
| `overlay_hello_world/overlay_hello_world/.env.example` | Packaged env example that only sets `ENABLED_SOLUTION_TAGS=hello-world` for installed-mode PHP discovery. |
| `overlay_hello_world/overlay_hello_world/README.md` | Packaged README for the reference hello-world overlay, describing archive contents and installed runtime expectations. |
| `overlay_hello_world/overlay_hello_world/RUNBOOK.md` | Packaged runbook defining the supported build, install, startup, and validation path for the hello-world overlay. |
| `overlay_hello_world/overlay_hello_world/docker-compose.overlay-hello-world.yaml` | Packaged compose overlay that customizes Airflow, Jupyter, and PHP for the installed hello-world runtime. |
| `overlay_hello_world/overlay_hello_world/docker/airflow/Dockerfile` | Packaged Airflow image extension adding Python dependencies used by the hello-world reference overlay. |
| `overlay_hello_world/overlay_hello_world/docker/jupyter/Dockerfile` | Packaged Jupyter image extension adding analysis and MinIO dependencies for hello-world validation. |
| `overlay_hello_world/overlay_hello_world/start-compose.sh` | Packaged start wrapper that launches the installed hello-world overlay through its compose file. |
| `overlay_hello_world/overlay_hello_world/stop-compose.sh` | Packaged stop wrapper that shuts down the installed hello-world overlay through its compose file. |
| `overlay_hello_world/php/solutions/hello_world_summary.php` | PHP solution page that renders the deterministic curated summary produced by the hello-world overlay. |
| `overlay_hello_world/scripts/hello_world_common.py` | Shared helper library for the hello-world overlay, resolving config, sample input, local mirrors, and optional object storage access. |
| `overlay_hello_world/scripts/hello_world_conformed_to_curated.py` | Reference curation script that computes the deterministic hello-world summary from the conformed payload. |
| `overlay_hello_world/scripts/hello_world_local_to_raw.py` | Reference ingestion script that copies the tracked sample payload into raw local and optional MinIO outputs. |
| `overlay_hello_world/scripts/hello_world_raw_to_conformed.py` | Reference transform script that normalizes raw hello-world records into deterministic conformed JSON. |
| **overlay_kaggle_ingestion/** |  |
| `overlay_kaggle_ingestion/.env.example` | Example env file for the Kaggle overlay, including local ports plus preferred and legacy Kaggle credential variables. |
| `overlay_kaggle_ingestion/README.md` | Compatibility README retained only to redirect readers to the packaged Kaggle overlay docs. |
| `overlay_kaggle_ingestion/RUNBOOK.md` | Compatibility runbook retained only to redirect readers to the packaged Kaggle overlay docs. |
| `overlay_kaggle_ingestion/config/kaggle_jobs.example.json` | Example job manifest defining dataset slug and raw/conformed/curated targets for Kaggle ingestion. |
| `overlay_kaggle_ingestion/dags/dag_kaggle_ingestion.py` | Thin Airflow DAG wrapper that runs the Kaggle raw, conformed, and curated scripts in sequence. |
| `overlay_kaggle_ingestion/dev-docker-compose.overlay-kaggle.yaml` | Development overlay Compose layer that injects Kaggle credentials, shared scripts, data mirrors, and tagged PHP output. |
| `overlay_kaggle_ingestion/dev-start-compose.sh` | Dev wrapper that starts the base stack with the Kaggle development overlay compose file attached. |
| `overlay_kaggle_ingestion/dev-stop-compose.sh` | Dev wrapper that stops the base stack with the Kaggle development overlay compose file attached. |
| `overlay_kaggle_ingestion/docker-compose.overlay-kaggle.yaml` | Source-tree installed-mode compose layer mirrored from the packaged Kaggle overlay for wrapper-based runtime testing. |
| `overlay_kaggle_ingestion/docker/airflow/Dockerfile` | Source-tree Airflow image extension for Kaggle ingestion, adding Kaggle and parquet dependencies. |
| `overlay_kaggle_ingestion/docker/jupyter/Dockerfile` | Source-tree Jupyter image extension for Kaggle validation notebooks and lightweight EDA. |
| `overlay_kaggle_ingestion/docs/explanation.md` | Architecture note describing the Kaggle overlay's config contract, pipeline stages, notebook role, and PHP surface. |
| `overlay_kaggle_ingestion/notebooks/kaggle_connectivity_and_eda.ipynb` | Validation notebook that checks Kaggle auth, MinIO artifacts, and lightweight EDA for the overlay. |
| `overlay_kaggle_ingestion/overlay_kaggle_ingestion/README.md` | Packaged README describing archive contents, install contract, and startup flow for `overlay_kaggle_ingestion_v1.0`. |
| `overlay_kaggle_ingestion/overlay_kaggle_ingestion/RUNBOOK.md` | Packaged runbook documenting the validated build, unzip, credential, startup, and stop path for this overlay. |
| `overlay_kaggle_ingestion/overlay_kaggle_ingestion/docker-compose.overlay-kaggle.yaml` | Packaged installed-mode Compose layer for Kaggle ingestion services, credentials, and PHP solution tagging. |
| `overlay_kaggle_ingestion/overlay_kaggle_ingestion/docker/airflow/Dockerfile` | Packaged Airflow image extension for Kaggle ingestion, adding Kaggle and parquet dependencies. |
| `overlay_kaggle_ingestion/overlay_kaggle_ingestion/docker/jupyter/Dockerfile` | Packaged Jupyter image extension for Kaggle validation notebooks and dataset inspection. |
| `overlay_kaggle_ingestion/overlay_kaggle_ingestion/start-compose.sh` | Packaged start wrapper that launches the installed Kaggle overlay through its compose file. |
| `overlay_kaggle_ingestion/overlay_kaggle_ingestion/stop-compose.sh` | Packaged stop wrapper that shuts down the installed Kaggle overlay through its compose file. |
| `overlay_kaggle_ingestion/php/solutions/dataset_summary.php` | PHP solution page that renders a curated Kaggle dataset summary JSON artifact, with an overridable summary path. |
| `overlay_kaggle_ingestion/scripts/conformed_to_curated.py` | CLI curation script that summarizes conformed Kaggle parquet data into curated JSON and a local mirror. |
| `overlay_kaggle_ingestion/scripts/kaggle_overlay_common.py` | Shared helper library for Kaggle ingestion, covering config loading, MinIO access, prefix normalization, and local mirrors. |
| `overlay_kaggle_ingestion/scripts/kaggle_to_raw.py` | CLI ingestion script that authenticates to Kaggle, downloads datasets, and uploads extracted files into raw storage. |
| `overlay_kaggle_ingestion/scripts/raw_to_conformed.py` | CLI transform script that standardizes raw Kaggle CSV objects into a conformed parquet output. |
| `overlay_kaggle_ingestion/start-compose.sh` | Source-tree installed-mode wrapper that starts the Kaggle overlay through the outer compose file. |
| `overlay_kaggle_ingestion/stop-compose.sh` | Source-tree installed-mode wrapper that stops the Kaggle overlay through the outer compose file. |
| **overlay_onlyoffice/** |  |
| `overlay_onlyoffice/README.md` | Main architecture note for the ONLYOFFICE and Nextcloud proof of concept, with MinIO retained as the system of record. |
| `overlay_onlyoffice/data/onlyoffice/community-prototype.docx` | Tracked sample DOCX used as the seed and fallback document for the ONLYOFFICE prototype. |
| `overlay_onlyoffice/data/onlyoffice/community-prototype.docx.version` | Tracked version counter file for the sample ONLYOFFICE prototype document; save callbacks increment it. |
| `overlay_onlyoffice/dev-docker-compose.overlay-onlyoffice.yaml` | Development compose layer that adds ONLYOFFICE Docs, Nextcloud, MinIO seeding, and related persistence services. |
| `overlay_onlyoffice/dev-start-compose.sh` | Dev wrapper that starts the base stack with the ONLYOFFICE proof-of-concept overlay attached. |
| `overlay_onlyoffice/dev-stop-compose.sh` | Dev wrapper that stops the base stack with the ONLYOFFICE proof-of-concept overlay attached. |
| `overlay_onlyoffice/php/inc/onlyoffice.php` | Legacy helper library for the earlier single-document ONLYOFFICE prototype, retained under `php/inc`. |
| `overlay_onlyoffice/php/onlyoffice/callback.php` | ONLYOFFICE callback endpoint that validates JWT and state tokens before accepting save callbacks. |
| `overlay_onlyoffice/php/onlyoffice/catalogue_helpers.php` | Helper library for browsing MinIO-backed documents and parsing selection metadata for the ONLYOFFICE PHP catalogue. |
| `overlay_onlyoffice/php/onlyoffice/documents.php` | Standalone PHP document catalogue that lists MinIO-backed editable documents and links into the ONLYOFFICE editor. |
| `overlay_onlyoffice/php/onlyoffice/download.php` | PHP download endpoint that streams either the selected MinIO document or the fallback tracked prototype file. |
| `overlay_onlyoffice/php/onlyoffice/editor.php` | Standalone ONLYOFFICE editor host page that builds runtime config for either the fallback or selected MinIO document. |
| `overlay_onlyoffice/php/onlyoffice/onlyoffice.php` | Authoritative ONLYOFFICE PHP helper library for runtime paths, JWT handling, MinIO access, and editor configuration. |
| `overlay_onlyoffice/php/solutions/onlyoffice_prototype.php` | PHP solution page exposing the ONLYOFFICE and Nextcloud proof-of-concept entry points and embedded editor status. |
| **php/** |  |
| `php/health.php` | PHP health page that probes core containers over TCP and HTTP from inside the PHP runtime. |
| `php/inc/layout.php` | Shared PHP layout template that supplies site chrome, metadata, and navigation for local service and solution pages. |
| `php/index.php` | PHP landing page listing local runtime service URLs and utility pages for the Community stack. |
| `php/solutions.php` | PHP discovery page that lists solution files and filters tagged overlays using `ENABLED_SOLUTION_TAGS`. |
| **scripts/** |  |
| `scripts/conformed_to_curated.py` | Installed-path Kaggle curation script carried-forward from the overlay package; expects `kaggle_overlay_common.py` beside it after unzip. |
| `scripts/raw_to_conformed.py` | Installed-path Kaggle transform script carried-forward from the overlay package; expects `kaggle_overlay_common.py` beside it after unzip. |

## Handoff And Runtime Coordination Documents

This repository currently has no tracked `docs/handoff/` coordination set; use the orientation documents below for session bootstrap.

| Document | Purpose | When to Read | Authority Type |
| --- | --- | --- | --- |
| `README.md` | Defines repository scope, non-goals, and the primary documentation entry points. | First, before reading implementation files. | Orientation entrypoint |
| `RUNBOOK.md` | Defines how to start, stop, reset, validate, and recover the base runtime. | Before operating the local stack. | Operational authority |
| `docs/HOWTO_OVERLAYS.md` | Defines the end-to-end workflow for creating, packaging, and validating overlays. | Before building or testing overlays. | Workflow guidance |
| `docs/architecture/overlay_contract_v1.md` | Defines the overlay filesystem contract and packaging rules overlays must satisfy. | Before changing overlay structure or compose behavior. | Architectural authority |
| `docs/releases/v1.1.0-overlay-contract-validation-and-installed-mode-stabilisation.md` | Records the validated release baseline and installed-mode outcomes for the overlay contract program. | When checking validated behavior or historical release scope. | Validated release record |

## Runtime Capability Status Model

No tracked `docs/handoff/runtime-capability-matrix.md` exists in this repository today; if one is added later, it should be the authoritative capability list.

| Status | Meaning |
| --- | --- |
| **COMPLETE / ACCEPTED** | Validated in the running local runtime with recorded evidence. Must not be reopened unless a specific regression, replacement, migration, or ADR-driven scope change is triggered. |
| **UNPROVEN / NOT ACCEPTED** | Not validated. Represents future activation work. Must not cast doubt on COMPLETE / ACCEPTED capabilities. |
| **DEFERRED** | Intentionally excluded from current scope. Requires a new ADR or explicit scope decision before any implementation begins. |
| **OPTIONAL MAINTENANCE** | Operational hygiene only. Does not affect capability status. |
