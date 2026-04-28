# Hello World Runtime Runbook

This runbook standardizes the operator path for the hello-world reference overlay.

## Dev / source-tree mode

From the repository root:

```bash
bash overlay_hello_world/dev-start-compose.sh
```

Stop:

```bash
bash overlay_hello_world/dev-stop-compose.sh
```

This dev path uses:

```bash
./start-compose.sh --overlay overlay_hello_world/dev-docker-compose.overlay-hello-world.yaml
```

## Build the archive

From the repository root:

```bash
cd overlay_hello_world
zip -rq ../overlay_hello_world_v1.0.zip \
  config scripts dags notebooks php data overlay_hello_world
```

## Install the overlay

Install the additive payload into a compatible repo root:

```bash
unzip -oq overlay_hello_world_v1.0.zip -d .
```

Optional config override:

```bash
cp config/hello_world_job.example.json config/hello_world_job.json
```

## Run the installed archive with the base stack

Start:

```bash
bash overlay_hello_world/start-compose.sh
```

This packaged wrapper uses:

```bash
./start-compose.sh --overlay overlay_hello_world/docker-compose.overlay-hello-world.yaml
```

Stop:

```bash
bash overlay_hello_world/stop-compose.sh
```

## Validate

This overlay is a compose-overlay example because it customises Airflow, Jupyter, and PHP service settings.

Validate:

- Airflow DAG `dag_hello_world`
- curated local mirror at `data/curated/hello_world/latest/summary.json`
- notebook `notebooks/hello_world_validation.ipynb`
- PHP page discovered through the Solutions UI when `ENABLED_SOLUTION_TAGS` includes `hello-world`

Trigger `dag_hello_world` manually in Airflow, or run the overlay scripts manually inside a compatible container.
