# TODO

## Documentation Gaps
- Align `../reference/CONTENTS.md` with the current repo structure (it references files that do not exist in this repo).
- Document the PHP service index and its port in `RUNBOOK.md`.
- Clarify the required `config/asx200_tickers.csv` file in top-level docs (not only in `config/README.md`).
- Document expected DAG schedules and dependencies in `dags/README.md`.

## Capability Gaps / Unclear Areas
- ASX backfill DAG relies on control/state objects in MinIO that are not created by default.
- Notebook outputs and dependencies are not verified against the running stack.
- No evidence of automated tests for DAG logic or data transformations.
- Airflow uses SQLite and SequentialExecutor; production-grade metadata and scaling are not implemented.

## Suggested Next Documentation Improvements
1) Add a minimal DAG catalog (one paragraph per DAG) to `dags/README.md`.
2) Add a short note in `RUNBOOK.md` about required config files and missing services referenced in `php/index.php`.

## Suggested Next Technical Clarifications
1) Add a checked-in example or generator for `config/asx200_tickers.csv` so the DAGs run without manual file creation.
2) Document how the backfill DAG should be configured and resumed (expected control files and S3 keys).
3) Add a simple validation script to confirm objects appear in `raw`, `conformed`, and `curated` after a run.
