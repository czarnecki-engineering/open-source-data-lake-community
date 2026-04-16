# DAG Execution Model Documentation Update

## Files updated
- `README.md`
- `RUNBOOK.md`
- `docs/dag-execution-model-doc-update.md`

## Summary of changes
- Added a concise `DAG Execution Model` section to `README.md`.
- Added a slightly more detailed operational `DAG Execution Model` section to `RUNBOOK.md`.
- Documented that heartbeat DAGs run automatically and are the platform health indicator.
- Documented that ASX DAGs are manual-trigger only, independent, and must be run in sequence by the operator.
- Documented that the ASX backfill DAG is manual-trigger only.
