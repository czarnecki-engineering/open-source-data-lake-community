Open Data Lake — Overlay Contract Specification

1. Purpose

An overlay is a packaged extension to an installed Open Data Lake instance.

It enables:
- addition of data pipelines (Airflow DAGs)
- supporting scripts and configuration
- notebooks for validation and exploration
- optional UI extensions (PHP landing pages)
- optional runtime configuration via environment variables

The overlay model is designed to be:
- filesystem-first
- portable across runtime environments
- simple to install (copy/unzip)
- composable (multiple overlays supported)


2. Core Principle

An overlay is a filesystem extension applied to a standard installation root.

All runtime behaviour derives from the filesystem and optional environment configuration.


3. Standard Installation Layout

A valid Open Data Lake installation exposes the following folders at its root:

config/
dags/
notebooks/
scripts/
data/
php/

Definitions:

config/      Configuration files (may include controlled mutable state)
dags/        Airflow DAG definitions
notebooks/   Jupyter notebooks
scripts/     Shared Python or utility code
data/        Local data outputs and working files
php/         Web UI assets (solution landing pages)

These folders define the overlay contract surface.


4. Overlay Structure

An overlay is developed in a project subfolder:

overlay_<name>/

Within that folder, the overlay may contain any subset of the standard folders:

overlay_<name>/
  config/
  dags/
  notebooks/
  scripts/
  data/
  php/

All folders are optional.


5. Installation Model

5.1 Installation Mechanism

An overlay is installed by copying its contents into the installation root:

cp -r overlay_<name>/* <installation_root>/

or via archive extraction:

unzip overlay_<name>.zip -d <installation_root>


5.2 Merge Behaviour

Overlay installation is additive with overwrite:

- Files not present in the installation root are added
- Files that already exist are overwritten by the overlay
- No deletion of existing files occurs


5.3 Multiple Overlays

Multiple overlays may be applied:

base
+ overlay A
+ overlay B

Rules:

- Overlays are applied in order
- Later overlays overwrite earlier overlays on conflict
- This behaviour is intentional and supported


6. Runtime Activation

6.1 Activation Mechanism

An overlay is activated at runtime using the base start scripts:

./start-<runtime>.sh --overlay <overlay>

Multiple overlays may be provided:

./start-<runtime>.sh --overlay overlayA --overlay overlayB


6.2 Overlay YAML

Overlay-specific runtime configuration (e.g. environment variables) may be defined using overlay YAML.

This YAML:
- must not modify base runtime definitions
- is limited to environment variables and service-specific overrides
- is optional

No additional overlay manifest format is defined.


7. Airflow Contract

7.1 Service Model

All environments must implement:

airflow-webserver
airflow-scheduler


7.2 Metadata Database

- The Airflow metadata database must be PostgreSQL
- SQLite is not part of the Supported runtime


7.3 Overlay Integration

Overlays interact with Airflow via filesystem:

dags/      DAG definitions
scripts/   shared code imported by DAGs
config/    configuration used by DAGs

No logical airflow service abstraction is part of the contract.


8. Configuration and State

8.1 Config Files

config/ contains:
- static configuration
- overlay-defined configuration files


8.2 Config-State

Overlays may define files in config/ that are both configuration and mutable runtime state.

Example:

config/jobs.json

Requirements:

- runtime must allow controlled write access where required
- file-based state must be preserved across runs

No alternative state model is required by the contract.


9. Data Contract

Overlays may assume the presence of standard object storage zones:

raw/
conformed/
curated/

These are typically implemented via MinIO or equivalent.


10. PHP UI Contract

10.1 Purpose

The php/ folder allows overlays to provide:
- a solution landing page
- lightweight UI for demonstration or interaction


10.2 Behaviour

- Files under php/ are served by the web component
- An overlay may provide a landing page (e.g. index.php)
- The runtime may expose these pages via a standard route


11. Secrets and Credentials

Overlays must not include real credentials.

They may include:
- placeholder values
- example configuration

Runtime environments are responsible for:
- injecting secrets
- mapping them to environment variables


12. Dependency Model

12.1 Base Runtime

The base runtime provides standard Python dependencies required for common overlays.


12.2 Overlay Extensions

If an overlay requires additional dependencies:
- this must be explicitly declared via runtime configuration or image extension
- it is not automatically inferred from the overlay filesystem


13. Runtime Independence

The overlay contract is independent of runtime implementation:

- Docker Compose
- Kubernetes
- future environments

All implementations must:
- expose the standard installation folders
- ensure those folders are visible to runtime services
- preserve overlay merge semantics


14. Non-Contract Elements

The following are not part of the overlay contract:

- logs/
- plugins/
- Airflow internal storage
- database storage
- MinIO internal storage
- service-specific working directories

These are managed by the base runtime.


15. Summary

An overlay is:

A filesystem-based extension that adds or overrides content
in a standard installation layout, activated at runtime via
optional configuration, and portable across environments.
