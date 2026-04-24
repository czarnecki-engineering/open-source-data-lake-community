# Contract

## Core Rules

- Overlays are additive only.
- Overlay archives must never overwrite protected root files.
- Overlay-authored files must be namespaced so path collisions are structurally unlikely.
- Archive writes are restricted to the explicit whitelist defined in `PATH_WHITELIST.md`.
- Overlay compose files are optional.
- v1 overlays may target only these known base services:
  - logical `airflow`
  - `jupyter`
  - `php`

## Protected Root Files

Overlays must not overwrite:

- `./start-compose.sh`
- `./stop-compose.sh`
- `./docker-compose.yaml`
- `./.env`
- `./README.md`
- `./RUNBOOK.md`

## Service-Specific Rules

- PHP is optional for general overlays.
- The hello-world reference overlay must include a PHP solution page.
- File-only overlays may omit a compose overlay file entirely.
- Compose overlays are merged in the order passed to repeated root-wrapper `--overlay` arguments.
- Overlay arguments accept either an explicit compose file path or an overlay name resolved by the root wrapper's documented file search order.
- When multiple overlays modify the same Compose settings, later overlays win according to Docker Compose merge behavior.
- Conflicting overlay service overrides are operator-managed.
- Airflow overlays must target logical service `airflow`, not the supported stack's internal Airflow service names.
- Airflow overlays may rely only on the logical `airflow` keys copied by compatibility support:
  - `build`
  - `image`
  - `environment`
  - `env_file`
  - `volumes`
  - `labels`
  - `pull_policy`
- Airflow overlays must not rely on unsupported logical `airflow` keys such as:
  - `command`
  - `ports`
- `depends_on`

## Wrapper Activation Rules

- Root wrappers may be called with zero or more `--overlay <compose-file-or-name>` arguments.
- Each `--overlay` value is resolved in this order when it is not already an existing file:
  - `overlay_<name>/dev-docker-compose.overlay-<slug>.yaml`
  - `overlay_<name>/docker-compose.overlay-<slug>.yaml`
  - `overlay_<name>/overlay_<name>/docker-compose.overlay-<slug>.yaml`
- Root wrappers generate one logical Airflow compatibility adapter from the final merged stack, not one adapter per overlay.
- Use the same overlay list and order for `stop-compose.sh` that was used for `start-compose.sh`.

## Packaging Shape

- Source-tree dev helpers may exist outside the nested packaged runtime folder.
- Packaged runtime files must live under `overlay_<name>/`.
- `.env.example` belongs inside the nested packaged runtime folder, not at archive root.
