# ONLYOFFICE Overlay

This overlay adds the ONLYOFFICE prototype workflow to the Community Edition stack.

## Purpose

It proves that the PHP service can host a page that launches ONLYOFFICE Docs, opens a single static `.docx` file from local storage, and receives save callbacks that write the edited document back to local disk.

Phase 2A extends the overlay with a MinIO-backed document catalogue at `/onlyoffice/documents.php`. The catalogue lists Office-compatible objects from a prototype `onlyoffice` bucket.

Phase 2B-R re-aligns the open workflow around object-store identity. The catalogue `Open` action passes `bucket` and `key` into the editor and download routes so the visible workflow remains `s3://bucket/key`, while the local fallback document remains available only for prototype validation.

Phase 2B-K keeps that object-store workflow intact while deriving the ONLYOFFICE document key from object revision metadata returned by the MinIO catalogue response, preferring `ETag` and falling back to `LastModified` when needed.

## Optional `.env` values

This overlay provides development defaults in
`overlay_onlyoffice/dev-docker-compose.overlay-onlyoffice.yaml`.

Set these values in the repository root `.env` only if you need to override the defaults:

```dotenv
ONLYOFFICE_DOCS_PORT=8090
ONLYOFFICE_DOCS_PUBLIC_URL=http://127.0.0.1:8090
ONLYOFFICE_STORAGE_INTERNAL_URL=http://php
ONLYOFFICE_JWT_SECRET=replace-with-a-long-random-secret
ONLYOFFICE_DOCUMENTS_BUCKET=onlyoffice
```

`ONLYOFFICE_DOCS_PUBLIC_URL` is used by the browser to load `api.js`.

`ONLYOFFICE_STORAGE_INTERNAL_URL` is used by ONLYOFFICE Docs to fetch the document and post save callbacks back to the PHP service over the internal Docker network.

## Local storage path

- Host path: `./overlay_onlyoffice/data/onlyoffice/`
- PHP container path: `/app/data/onlyoffice/`

The prototype stores:

- `community-prototype.docx`
- `community-prototype.docx.version`

Local runtime files may be created under `/app/data/onlyoffice/runtime/` for internal callback handling, but MinIO/S3 remains the intended source of truth for catalogue-selected documents.

## MinIO prototype bucket

On overlay startup, `onlyoffice-minio-init` creates a dedicated prototype bucket and uploads:

- `s3://onlyoffice/community-prototype.docx`

This keeps ONLYOFFICE documents separate from the existing `raw`, `conformed`, and `curated` data-lake buckets.

Save-back of edited MinIO/S3 objects remains Phase 2C. Phase 2B-R does not introduce a local working document as the user-facing source of truth.

## Run with the overlay

```bash
./start-compose.sh --overlay onlyoffice
```

Or use the overlay wrapper:

```bash
bash overlay_onlyoffice/dev-start-compose.sh
```
