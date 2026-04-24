# Execution Rules

## Dev Mode

- Run source-tree dev wrappers from the repository root.
- Dev wrappers must pass an explicit compose file path to the root wrapper scripts.
- Dev wrappers must fail clearly when run from the wrong location.

## Packaged Mode

- Run packaged wrappers from the installed repository root.
- Packaged wrappers must pass an explicit compose file path to the root wrapper scripts.
- Packaged wrappers must refer to the packaged runtime compose path under `overlay_<name>/`.
- File-only packaged overlays may omit packaged wrappers entirely and rely on the base root wrappers.

## General

- Do not rely on overlay name auto-discovery when writing overlay wrappers.
- Do not call Docker directly from overlay wrappers when the root wrapper already encapsulates supported behavior.
- Root wrappers accept zero or more `--overlay <compose-file-or-name>` arguments.
- If a `--overlay` value is not an existing file, the root wrapper resolves it in this order:
  - `overlay_<name>/dev-docker-compose.overlay-<slug>.yaml`
  - `overlay_<name>/docker-compose.overlay-<slug>.yaml`
  - `overlay_<name>/overlay_<name>/docker-compose.overlay-<slug>.yaml`
- Root wrappers merge overlays in the order the arguments are provided.
- Use the same overlay list and order for `stop-compose.sh` that was used for `start-compose.sh`.

Examples:

- `./start-compose.sh`
- `./start-compose.sh --overlay hello_world`
- `./start-compose.sh --overlay prices --overlay hello_world`
- `./stop-compose.sh --overlay prices --overlay hello_world`
