# Hello World Runtime Overlay

This is the packaged runtime folder for the hello-world reference overlay.

It is the reference compose-overlay example for the Community runtime contract.

Runtime surfaces assumed after install:

- `config/hello_world_job.example.json`
- `scripts/hello_world_*.py`
- `dags/dag_hello_world.py`
- `notebooks/hello_world_validation.ipynb`
- `php/solutions/hello_world_summary.php`
- `data/sample/hello_world/hello_world_input.json`

## Dev / source-tree mode

From the repository root:

```bash
bash overlay_hello_world/dev-start-compose.sh
```

Stop:

```bash
bash overlay_hello_world/dev-stop-compose.sh
```

This dev path activates:

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

## Install from archive

From the root of a compatible Community checkout:

```bash
unzip -oq overlay_hello_world_v1.0.zip -d .
```

Optional config override:

```bash
cp config/hello_world_job.example.json config/hello_world_job.json
```

## Run the installed overlay with the base stack

Start with:

```bash
bash overlay_hello_world/start-compose.sh
```

This packaged wrapper runs the base root wrapper with:

```bash
./start-compose.sh --overlay overlay_hello_world/docker-compose.overlay-hello-world.yaml
```

Stop with:

```bash
bash overlay_hello_world/stop-compose.sh
```

## Validate

Check:

- Airflow DAG `dag_hello_world`
- curated local mirror at `data/curated/hello_world/latest/summary.json`
- notebook `notebooks/hello_world_validation.ipynb`
- PHP page in the Solutions UI when `ENABLED_SOLUTION_TAGS` includes `hello-world`
