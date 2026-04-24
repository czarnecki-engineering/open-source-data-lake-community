# Archive Rules

Overlay archives are built from the outer overlay source-tree folder.

## Compose-Overlay Example

The v1 hello-world reference overlay is archived from the outer `overlay_hello_world/` folder.

Archive command:

```bash
cd overlay_hello_world
zip -rq ../overlay_hello_world_v1.0.zip \
  config scripts dags notebooks php data overlay_hello_world
```

## File-Only Example

The minimal file-only example overlay is archived from the outer `overlay_file_only_demo/` folder.

Archive command:

```bash
cd overlay_file_only_demo
zip -rq ../overlay_file_only_demo_v1.0.zip \
  php overlay_file_only_demo
```

## Required Rule

The published runtime archive must contain only:

- additive runtime payload
- the nested packaged runtime folder under `overlay_<name>/`

## The Archive Must Not Include

- `dev-start-compose.sh`
- `dev-stop-compose.sh`
- `dev-docker-compose.overlay-hello-world.yaml`
- any root `.env.example`
- any protected base file from the install target

Interpretation:

- source-tree dev helpers may exist in git
- the published runtime archive must contain only additive runtime payload plus the nested packaged runtime folder
- file-only overlays may omit compose YAML, packaged wrappers, `.env.example`, and Dockerfiles
