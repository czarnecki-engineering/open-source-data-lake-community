# Path Whitelist

Overlay archive writes are restricted to explicitly allowed additive paths.

Allowed root-level path families:

- `./config/<overlay>*.json`
- `./scripts/<overlay>*.py`
- `./dags/dag_<overlay>*.py`
- `./notebooks/<overlay>*.ipynb`
- `./php/solutions/<overlay>*.php`
- `./data/sample/<overlay>/**`
- `./overlay_<name>/**`

For the hello-world reference overlay, the concrete allowed payload paths are:

- `./config/hello_world_job.example.json`
- `./scripts/hello_world_common.py`
- `./scripts/hello_world_local_to_raw.py`
- `./scripts/hello_world_raw_to_conformed.py`
- `./scripts/hello_world_conformed_to_curated.py`
- `./dags/dag_hello_world.py`
- `./notebooks/hello_world_validation.ipynb`
- `./php/solutions/hello_world_summary.php`
- `./data/sample/hello_world/hello_world_input.json`
- `./overlay_hello_world/**`

Anything outside this whitelist is out of contract for v1.
