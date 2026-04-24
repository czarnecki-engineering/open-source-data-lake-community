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
