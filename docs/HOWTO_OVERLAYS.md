# HOWTO_OVERLAYS

## Purpose

This guide explains how to build, package, install, and validate overlays in this repository. Use it for workflow; use [overlay_contract_v1.md](architecture/overlay_contract_v1.md) for rules.

## Prerequisites

- Repository checked out locally
- Docker Engine and Docker Compose v2 available
- Repository root `.env` created from `.env.example`
- Base runtime commands available from the repository root:
  - `./start-compose.sh`
  - `./stop-compose.sh`

## Step 1 — Create overlay

Create the overlay workspace from the repository root:

```bash
mkdir -p overlay_x/overlay_x overlay_x/docs
```

Add only the standard runtime folders your overlay needs under `overlay_x/`:

```text
overlay_x/
  config/
  dags/
  notebooks/
  scripts/
  data/
  php/
  overlay_x/
  docs/
```

Use `overlay_x/overlay_x/README.md` and `overlay_x/overlay_x/RUNBOOK.md` for packaged overlay documentation.

## Step 2 — Develop overlay

Add overlay files under `overlay_x/`. Keep the packaged runtime content inside `overlay_x/overlay_x/`, and keep optional explanation material under `overlay_x/docs/`.

Follow the contract while designing the overlay structure and runtime behavior:

- [overlay_contract_v1.md](architecture/overlay_contract_v1.md)

If the overlay needs a development Compose layer, create:

```text
overlay_x/dev-docker-compose.overlay-x.yaml
```

If the overlay needs an installed-mode Compose layer, package:

```text
overlay_x/overlay_x/docker-compose.overlay-x.yaml
```

## Step 3 — Run in development mode

Start the base system from the repository root:

```bash
./start-compose.sh
```

If the overlay has a development Compose file, restart with the overlay attached:

```bash
./stop-compose.sh
./start-compose.sh --overlay x
```

The `--overlay x` form resolves `overlay_x/dev-docker-compose.overlay-x.yaml` automatically. You can also pass the file path directly:

```bash
./start-compose.sh --overlay overlay_x/dev-docker-compose.overlay-x.yaml
```

Verify the overlay is loaded by checking the services and overlay-delivered assets:

```bash
docker ps --format '{{.Names}}: {{.Status}}' | sort
docker compose -f docker-compose.yaml -f overlay_x/dev-docker-compose.overlay-x.yaml config --services
```

Then confirm the expected DAGs, notebooks, PHP pages, or scripts appear in the running stack.

## Step 4 — Test overlay

Confirm the development workflow behaves as expected:

- Services start and stop cleanly
- Overlay DAGs appear in Airflow
- Expected files or data paths appear in MinIO, notebooks, or PHP pages
- Base runtime behavior still works without unexpected regressions

Use the smallest practical end-to-end checks. Typical commands:

```bash
docker logs airflow-webserver --tail 100
docker logs airflow-scheduler --tail 100
docker logs minio --tail 100
```

If the overlay uses notebooks or UI pages, open the corresponding service URLs from the running stack and confirm the overlay content is present.

## Step 5 — Package overlay

Build the archive from the repository root after development-mode validation succeeds:

```bash
cd overlay_x
zip -rq ../overlay_x_v1.0.zip overlay_x docs config dags notebooks scripts data php
cd ..
```

If your overlay does not use every standard folder, omit the folders that are not present. Before publishing the archive, confirm that it contains the packaged runtime folder and any overlay content required at install time.

## Step 6 — Install overlay

Install the archive into a compatible Open Data Lake checkout root:

```bash
unzip -oq overlay_x_v1.0.zip -d /path/to/open-data-lake
```

This should install the packaged overlay directory and any overlay content into the target repository root.

## Step 7 — Run in installed mode

From the target repository root, start the system with the installed overlay:

```bash
./start-compose.sh --overlay x
```

If the overlay ships a wrapper script, use that wrapper instead:

```bash
bash overlay_x/start-compose.sh
```

Verify that installed-mode behavior matches development mode:

- The same services start
- The same overlay content is visible
- The same validation steps succeed

Stop the installed overlay with the matching stop path:

```bash
./stop-compose.sh --overlay x
```

## Step 8 — Validate against contract

Confirm the overlay structure and behavior align with:

- [overlay_contract_v1.md](architecture/overlay_contract_v1.md)

Check:

- Archive contents match the intended install layout
- Overlay startup uses supported services and paths
- Installed-mode validation matches the packaged overlay documentation

## Troubleshooting

- If `./start-compose.sh --overlay x` fails, pass the full overlay Compose path and confirm the file exists.
- If Docker startup fails, fix `.env` first, then rerun the base stack before retesting the overlay.
- If installed mode differs from development mode, inspect the archive contents and the packaged `overlay_x/README.md` and `overlay_x/RUNBOOK.md`.
