# Reference Layout

Full compose-overlay layout:

```text
overlay_<name>/
  dev-start-compose.sh
  dev-stop-compose.sh
  dev-docker-compose.overlay-<name>.yaml

  config/
  scripts/
  dags/
  notebooks/
  php/
    solutions/
  data/
    sample/
  docs/

  overlay_<name>/
    start-compose.sh
    stop-compose.sh
    docker-compose.overlay-<name>.yaml
    README.md
    RUNBOOK.md
    .env.example
    docker/
      airflow/
        Dockerfile
      jupyter/
        Dockerfile
```

Interpretation:

- the outer folder is the source-tree and archive build root
- the nested `overlay_<name>/` folder is the packaged runtime folder
- dev helpers stay outside the nested packaged runtime folder

Minimal file-only layout:

```text
overlay_<name>/
  php/
    solutions/
      <overlay>_*.php

  overlay_<name>/
    README.md
    RUNBOOK.md
```

Interpretation:

- file-only overlays may omit dev wrappers, packaged wrappers, `.env.example`, Dockerfiles, and compose YAML
- file-only overlays run through the base root wrappers with no `--overlay` argument
