# Hello World Runtime Runbook

1. Install the additive payload into a compatible repo root.
2. Optionally copy `config/hello_world_job.example.json` to `config/hello_world_job.json` to override defaults.
3. Start the stack with `bash overlay_hello_world/start-compose.sh`.
4. This overlay is a compose-overlay example because it customises Airflow, Jupyter, and PHP service settings. Simpler file-only overlays do not need an overlay compose file.
5. Trigger `dag_hello_world` manually in Airflow, or run the overlay scripts manually inside a compatible container.
6. Validate:
  - curated local mirror at `data/curated/hello_world/latest/summary.json`
  - notebook `notebooks/hello_world_validation.ipynb`
  - PHP page discovered through the Solutions UI when `ENABLED_SOLUTION_TAGS` includes `hello-world`
