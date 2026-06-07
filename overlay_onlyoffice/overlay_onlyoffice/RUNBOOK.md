# ONLYOFFICE Runtime Runbook

## Dev / source-tree mode

From the repository root:

```bash
bash overlay_onlyoffice/dev-start-compose.sh
```

Stop:

```bash
bash overlay_onlyoffice/dev-stop-compose.sh
```

This dev path activates:

```bash
./start-compose.sh --overlay overlay_onlyoffice/dev-docker-compose.overlay-onlyoffice.yaml
```

## Build the archive

From the repository root:

```bash
cd overlay_onlyoffice
zip -rq ../overlay_onlyoffice_v1.0.zip php data overlay_onlyoffice
```

## Install the overlay

From the root of a compatible Community checkout:

```bash
unzip -oq overlay_onlyoffice_v1.0.zip -d .
```

## Run the installed archive with the base stack

Start:

```bash
bash overlay_onlyoffice/start-compose.sh
```

This packaged wrapper uses:

```bash
./start-compose.sh --overlay overlay_onlyoffice/docker-compose.overlay-onlyoffice.yaml
```

Stop:

```bash
bash overlay_onlyoffice/stop-compose.sh
```

## Validate

Check:

- PHP solution page in the Solutions UI when `ENABLED_SOLUTION_TAGS` includes `onlyoffice`
- document catalogue at `/onlyoffice/documents.php`
- standalone editor at `/onlyoffice/editor.php`
- Nextcloud at `http://127.0.0.1:${NEXTCLOUD_PORT:-8091}`
- ONLYOFFICE Docs at `http://127.0.0.1:${ONLYOFFICE_DOCS_PORT:-8090}`
