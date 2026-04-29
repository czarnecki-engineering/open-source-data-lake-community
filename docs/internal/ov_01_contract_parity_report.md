# OV-01 — Contract Parity Report

## Branch Verification
- Community: feature/rearchitecture-runtime-overlay-contract
- Supported: feature/rearchitecture-runtime-overlay-contract

## File Paths
- Community: /Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docs/architecture/overlay_contract_v1.md
- Supported: /Users/marekczarnecki/Documents/GitHub/open-source-data-lake-supported/docs/architecture/overlay_contract_v1.md

## Hash Comparison
- Community SHA: 03c4541e5e17d3ab15d108c4037608b72c73408b
- Supported SHA: b4cbdc45446bb08da0de3aae25a125b1a5ad5280
- Result: DIFFERENT

Semantic confirmation: DIFFERENT. The files are not byte-identical, and the diff shows meaningfully different contract language around overlay limits, required service names, metadata database requirements, and overlay targeting rules.

## Diff Output
```diff
--- /Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/docs/architecture/overlay_contract_v1.md	2026-04-29 08:22:59
+++ /Users/marekczarnecki/Documents/GitHub/open-source-data-lake-supported/docs/architecture/overlay_contract_v1.md	2026-04-29 19:50:52
@@ -123,7 +123,7 @@
 
 This YAML:
 - must not modify base runtime definitions
-- is limited to environment variables and service-specific overrides
+- must be limited to environment variables and explicit service-specific overrides against services that exist in the base runtime
 - is optional
 
 No additional overlay manifest format is defined.
@@ -133,16 +133,18 @@
 
 7.1 Service Model
 
-All environments must implement:
+All environments must implement the explicit Airflow runtime services:
 
 airflow-webserver
 airflow-scheduler
 
+The logical `airflow` service does not exist and must not be referenced by overlays or overlay runtime configuration.
 
+
 7.2 Metadata Database
 
-- The Airflow metadata database must be PostgreSQL
-- SQLite is not part of the Supported runtime
+- The Supported runtime must use PostgreSQL for the Airflow metadata database
+- SQLite is not permitted in the Supported runtime
 
 
 7.3 Overlay Integration
@@ -153,9 +155,11 @@
 scripts/   shared code imported by DAGs
 config/    configuration used by DAGs
 
-No logical airflow service abstraction is part of the contract.
+Overlays that apply runtime configuration must target explicit base-runtime services such as `airflow-webserver` and `airflow-scheduler`.
 
+Overlays must not introduce or depend on service abstractions that are not present in the base runtime.
 
+
 8. Configuration and State
 
 8.1 Config Files
```
