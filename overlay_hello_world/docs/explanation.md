# Hello World Overlay Explanation

This overlay is the minimal executable reference implementation for the generic overlay contract.

It demonstrates:

- deterministic local sample input
- three stage data flow from local sample to raw, conformed, and curated outputs
- optional writes to MinIO buckets when S3 environment variables are available
- local mirror outputs under `data/raw/hello_world`, `data/conformed/hello_world`, and `data/curated/hello_world`
- a PHP solution page and notebook that consume the curated summary

Source-tree dev overlay behavior:

- dev mode uses directory-level mounts only
- dev mode replaces the container views of `dags/`, `scripts/`, `notebooks/`, and `php/solutions/` with the overlay source-tree directories
- this avoids fragile file-level mounts into base-mounted directories on Docker Desktop and similar runtimes
- while dev mode is active, the base stack's other DAGs and PHP solution pages are not the active in-container view
- packaged mode is unchanged and still assumes installed root payload paths

Expected curated values:

- `record_count = 4`
- `total_amount = 100`
- `category_counts = {"alpha": 2, "beta": 1, "gamma": 1}`
- `minimum_date = 2026-01-10`
- `maximum_date = 2026-01-13`
- `run_date = 2026-04-24`
