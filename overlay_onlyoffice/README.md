# ONLYOFFICE Overlay

This overlay adds a minimal Phase 1 local-file ONLYOFFICE prototype to the Community Edition stack.

## Purpose

It proves that the PHP service can host a page that launches ONLYOFFICE Docs, opens a single static `.docx` file from local storage, and receives save callbacks that write the edited document back to local disk.

## Optional `.env` values

This overlay provides development defaults in
`overlay_onlyoffice/dev-docker-compose.overlay-onlyoffice.yaml`.

Set these values in the repository root `.env` only if you need to override the defaults:

```dotenv
ONLYOFFICE_DOCS_PORT=8090
ONLYOFFICE_DOCS_PUBLIC_URL=http://127.0.0.1:8090
ONLYOFFICE_STORAGE_INTERNAL_URL=http://php
ONLYOFFICE_JWT_SECRET=replace-with-a-long-random-secret
```

`ONLYOFFICE_DOCS_PUBLIC_URL` is used by the browser to load `api.js`.

`ONLYOFFICE_STORAGE_INTERNAL_URL` is used by ONLYOFFICE Docs to fetch the document and post save callbacks back to the PHP service over the internal Docker network.

## Local storage path

- Host path: `./overlay_onlyoffice/data/onlyoffice/`
- PHP container path: `/app/data/onlyoffice/`

The prototype stores:

- `community-prototype.docx`
- `community-prototype.docx.version`

## Run with the overlay

```bash
./start-compose.sh --overlay onlyoffice
```

Or use the overlay wrapper:

```bash
bash overlay_onlyoffice/dev-start-compose.sh
```
