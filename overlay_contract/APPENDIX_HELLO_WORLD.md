# Hello World Appendix

`overlay_hello_world/` is the minimal executable reference overlay for this contract.

It demonstrates:

- deterministic local sample input
- three-step Airflow execution using overlay scripts
- local mirror outputs under `data/raw`, `data/conformed`, and `data/curated`
- optional MinIO writes when S3 environment variables are available
- a notebook that validates the curated output
- a PHP solution page gated by `ENABLED_SOLUTION_TAGS=hello-world`

The reference overlay is intentionally simple:

- no public internet access
- no new long-running services
- no dependency on unsupported Airflow compatibility keys
