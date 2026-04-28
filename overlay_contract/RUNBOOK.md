# Overlay Contract Runbook

Use this sequence when implementing a new overlay against the supported stack.

1. Keep the overlay additive only. Do not modify protected base files.
2. Put overlay runtime payload under namespaced paths such as `config/<overlay>_*.json`, `scripts/<overlay>_*.py`, `dags/dag_<overlay>.py`, `php/solutions/<overlay>_*.php`, and `data/sample/<overlay>/...`.
3. Target only the v1 supported services:
   - logical `airflow`
   - `jupyter`
   - `php`
4. If the overlay customises Airflow, target logical service `airflow` only. Do not reference `airflow-webserver`, `airflow-scheduler`, or `airflow-user-init`.
5. Use explicit compose file paths in overlay wrapper scripts. Do not rely on overlay name discovery.
6. Compose overlays are optional. If the overlay only installs additive runtime files, omit compose YAML and use the base root wrappers directly.
7. If the overlay needs service changes, keep those changes in an optional compose overlay file under `overlay_<name>/`.
8. If multiple compose overlays are activated together, assume later overlays win where Docker Compose merge behavior resolves conflicts.
9. Keep packaged runtime files under `overlay_<name>/` and keep source-tree dev helpers outside that nested runtime folder.
10. Validate the overlay with both:
   - source-tree dev compose
   - packaged runtime compose
11. Before publishing, re-check `CHECKLIST.md`, `INSTALL_RULES.md`, and `ARCHIVE_RULES.md`.

## Documentation Standard

Packaged runtime docs should be predictable across overlays.

Every overlay should include:

- `overlay_<name>/README.md`
- `overlay_<name>/RUNBOOK.md`

Those docs should clearly cover:

1. what the overlay does
2. how to run it in source-tree dev mode
3. how to build the archive
4. how to install the overlay into a compatible repo root
5. how to start the installed overlay with the base stack
6. how to stop the installed overlay
7. how to validate the installed result

For file-only overlays:

- the dev-mode section may explicitly say that no separate dev wrapper exists
- the installed-runtime section should explicitly say to use the normal base root wrappers

For compose overlays:

- the docs should name the exact `dev-start-compose.sh` and `dev-stop-compose.sh` commands
- the docs should name the exact packaged `start-compose.sh` and `stop-compose.sh` commands
- if the packaged wrapper delegates to the root wrapper, say so directly
