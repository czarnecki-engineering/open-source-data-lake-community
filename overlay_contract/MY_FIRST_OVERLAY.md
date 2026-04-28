# My First Overlay

This is the shortest path to a working overlay.

Start with a file-only overlay.

A file-only overlay:

- adds files only under the normal runtime folders
- does not change Docker services
- does not need an overlay compose file
- does not need overlay start/stop wrapper scripts
- runs with the normal root command:
  - `./start-compose.sh`

## Smallest Useful Example

The smallest useful overlay is one PHP solution page plus packaged docs.

Example source tree:

```text
overlay_file_only_demo/
  php/
    solutions/
      file_only_demo.php

  overlay_file_only_demo/
    README.md
    RUNBOOK.md
```

What happens after install:

- `overlay_file_only_demo/php/solutions/file_only_demo.php` becomes `php/solutions/file_only_demo.php`
- `overlay_file_only_demo/overlay_file_only_demo/README.md` becomes `overlay_file_only_demo/README.md`
- `overlay_file_only_demo/overlay_file_only_demo/RUNBOOK.md` becomes `overlay_file_only_demo/RUNBOOK.md`

After that, start the normal base stack:

```bash
./start-compose.sh
```

No `--overlay` argument is needed because the base PHP container already mounts `./php`.

Even the smallest overlay should document the standard operator questions in packaged docs:

- dev mode: for file-only overlays, explicitly say there is no separate dev wrapper
- archive build: show the exact archive command
- install: show the exact additive unzip command
- installed runtime: show the exact base start command

## When You Need Compose YAML

Add `docker-compose.overlay-<name>.yaml` only if the overlay must change service definitions, for example:

- a different Airflow image or Dockerfile
- a different Jupyter image or Dockerfile
- extra service environment variables
- extra service volumes
- PHP `ENABLED_SOLUTION_TAGS`

If you need those changes, use a compose overlay and activate it with:

```bash
./start-compose.sh --overlay <compose-file-or-name>
```

Multiple compose overlays are allowed:

```bash
./start-compose.sh --overlay overlay_a --overlay overlay_b
```

The merge order is left to right. Later overlays win where Docker Compose says later values win.

## Practical Author Workflow

1. Start with plain runtime files under namespaced paths.
2. Check whether the base mounts already expose those files to the service that needs them.
3. If yes, stop there. Do not create compose YAML.
4. Add packaged docs under `overlay_<name>/`.
   Those docs should answer dev mode, archive build, install, and installed-runtime startup explicitly.
5. Archive only the additive payload plus the packaged docs folder.
6. Install into a compatible repo root and test with plain `./start-compose.sh`.
7. Only add compose YAML later if the overlay truly needs service changes.

## Reference Examples In This Repo

- `overlay_file_only_demo/` for a minimal file-only overlay
- `overlay_hello_world/` for a compose-overlay example
