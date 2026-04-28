# File Only Demo Runbook

## Dev / source-tree mode

This overlay has no separate dev wrapper.

Because it is file-only, use the normal base stack command during development:

```bash
./start-compose.sh
```

## Build the archive

From the repository root:

```bash
cd overlay_file_only_demo
zip -rq ../overlay_file_only_demo_v1.0.zip php overlay_file_only_demo
```

## Install the overlay

Install the additive payload into a compatible repo root:

```bash
unzip -oq overlay_file_only_demo_v1.0.zip -d .
```

## Run the installed archive with the base stack

Start the normal base stack:

```bash
./start-compose.sh
```

Stop with the normal base stop command:

```bash
./stop-compose.sh
```

## Validate

1. Open the Solutions page.
2. Confirm that `File Only Demo` is listed.

This example is intentionally file-only:

- no `--overlay` argument
- no overlay compose YAML
- no overlay wrapper scripts
