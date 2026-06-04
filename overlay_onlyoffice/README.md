# ONLYOFFICE Overlay

This overlay now provides a controlled ONLYOFFICE plus Nextcloud proof of concept on top of the existing Community Edition stack.

## Architecture Summary

The overlay keeps the existing PHP document catalogue, MinIO service, and ONLYOFFICE Docs service in place.

Nextcloud is added as a parallel UI and orchestration layer:

- Existing PHP catalogue remains available at the existing PHP service.
- Existing MinIO bucket `s3://onlyoffice/...` remains the system of record.
- Nextcloud mounts that bucket through External Storage Support.
- ONLYOFFICE Docs is reused as the document editor for files opened from Nextcloud.
- Edited documents are expected to save back through Nextcloud into the same MinIO-backed external storage mount.

This POC does not configure MinIO as Nextcloud primary object storage.

## Added Services

The overlay now adds these overlay-local services:

- `nextcloud`
- `nextcloud-db`
- `nextcloud-redis`
- `nextcloud-cron`

Existing overlay services remain:

- `onlyoffice-minio-init`
- `onlyoffice-docs`
- `php`

## Added Ports

- Nextcloud browser port: `${NEXTCLOUD_PORT:-8091}:80`
- ONLYOFFICE Docs browser port remains: `${ONLYOFFICE_DOCS_PORT:-8090}:80`

No host ports are exposed for:

- `nextcloud-db`
- `nextcloud-redis`

## Added Volumes

Nextcloud persistence is stored in named volumes:

- `nextcloud-db-data`
- `nextcloud-custom-apps`
- `nextcloud-config`
- `nextcloud-data`

The existing overlay bind mounts for PHP and the seeded ONLYOFFICE prototype document remain unchanged.

The Nextcloud application code itself is not persisted as a named volume.
This avoids bootstrap drift between a recreated code volume and an existing persisted config volume.

## Environment Variable Defaults

This overlay uses Compose defaults inside `overlay_onlyoffice/dev-docker-compose.overlay-onlyoffice.yaml`.

Override in the repository root `.env` only if needed:

```dotenv
ONLYOFFICE_DOCS_PORT=8090
ONLYOFFICE_DOCS_PUBLIC_URL=http://127.0.0.1:8090
ONLYOFFICE_STORAGE_INTERNAL_URL=http://php
ONLYOFFICE_JWT_SECRET=change-me-onlyoffice-dev-secret
ONLYOFFICE_CALLBACK_STATE_SECRET=replace-with-a-separate-secret-if-desired
ONLYOFFICE_DOCUMENTS_BUCKET=onlyoffice

NEXTCLOUD_PORT=8091
NEXTCLOUD_ADMIN_USER=admin
NEXTCLOUD_ADMIN_PASSWORD=admin123
NEXTCLOUD_DB_NAME=nextcloud
NEXTCLOUD_DB_USER=nextcloud
NEXTCLOUD_DB_PASSWORD=nextcloud-dev-password
NEXTCLOUD_TRUSTED_DOMAINS=127.0.0.1 localhost nextcloud
NEXTCLOUD_OVERWRITEHOST=127.0.0.1:8091
NEXTCLOUD_OVERWRITEPROTOCOL=http
NEXTCLOUD_REDIS_HOST=nextcloud-redis
```

## Startup Command

Use the existing base plus overlay lifecycle:

```bash
./start-compose.sh --overlay onlyoffice
```

Or use the overlay wrapper:

```bash
bash overlay_onlyoffice/dev-start-compose.sh
```

Equivalent Compose validation pattern:

```bash
docker compose -f docker-compose.yaml -f overlay_onlyoffice/dev-docker-compose.overlay-onlyoffice.yaml config
```

## Access URLs

Browser-facing URLs:

- PHP document catalogue: `http://127.0.0.1:8088/onlyoffice/documents.php`
- Nextcloud: `http://127.0.0.1:${NEXTCLOUD_PORT:-8091}`
- ONLYOFFICE Docs: `http://127.0.0.1:${ONLYOFFICE_DOCS_PORT:-8090}`
- MinIO Console: `http://127.0.0.1:9001`

Internal container-to-container URLs:

- Nextcloud to ONLYOFFICE Docs: `http://onlyoffice-docs/`
- ONLYOFFICE callback back to Nextcloud: `http://nextcloud/`
- Nextcloud to MinIO: `http://minio:9000`

Do not use `localhost` for container-internal service configuration.

## Existing ONLYOFFICE Prototype Storage

The overlay still seeds the dedicated prototype MinIO bucket and uploads:

- `s3://${ONLYOFFICE_DOCUMENTS_BUCKET:-onlyoffice}/community-prototype.docx`

The PHP-only document workflow remains available in parallel.

## Nextcloud First Run

1. Start the stack with the overlay.
2. Open `http://127.0.0.1:${NEXTCLOUD_PORT:-8091}`.
3. Log in with:

- Username: `${NEXTCLOUD_ADMIN_USER:-admin}`
- Password: `${NEXTCLOUD_ADMIN_PASSWORD:-admin123}`

The container uses standard first-run environment bootstrap for the initial admin account and PostgreSQL connection.

## Manual External Storage Support Configuration

This POC intentionally keeps app enablement as a manual admin step instead of brittle automation.

1. In Nextcloud, open `Apps`.
2. Enable `External storage support`.
3. If the ONLYOFFICE connector is available, enable `ONLYOFFICE`.
4. If the ONLYOFFICE connector is not available, install it through the Nextcloud app flow first.

## Manual MinIO S3-Compatible Mount Configuration

Create the external storage mount in Nextcloud admin settings with these values:

- Storage type: `Amazon S3`
- Bucket: `${ONLYOFFICE_DOCUMENTS_BUCKET:-onlyoffice}`
- Hostname: `minio:9000`
- Port: `9000`
- Region: `us-east-1`
- Access key: existing `${MINIO_ROOT_USER}` value
- Secret key: existing `${MINIO_ROOT_PASSWORD}` value
- Use path style: enabled
- Use SSL: disabled
- Root path: leave empty unless you intentionally want a bucket subpath

Equivalent endpoint reference for reasoning and troubleshooting:

- `http://minio:9000`

After saving the mount, existing bucket objects should be visible from day one.

## Manual ONLYOFFICE Connector Configuration

Configure the Nextcloud ONLYOFFICE connector with these values:

- Document Editing Service address for users: `http://127.0.0.1:${ONLYOFFICE_DOCS_PORT:-8090}`
- Document Editing Service address from the server: `http://onlyoffice-docs/`
- Server address for internal requests from ONLYOFFICE Docs: `http://nextcloud/`
- Secret key: `${ONLYOFFICE_JWT_SECRET:-change-me-onlyoffice-dev-secret}`

The same JWT secret must match the existing `onlyoffice-docs` container configuration.

## Validation Steps

1. Start the stack.
2. Confirm the existing PHP document catalogue still loads.
3. Confirm Nextcloud loads at `http://127.0.0.1:${NEXTCLOUD_PORT:-8091}`.
4. Enable `External storage support`.
5. Add the MinIO S3-compatible mount.
6. Confirm `community-prototype.docx` appears in Nextcloud Files.
7. Enable and configure the ONLYOFFICE connector.
8. Open the document from Nextcloud.
9. Save the document and confirm the object remains in the same MinIO bucket path.

## Known Limitations

- External Storage Support and ONLYOFFICE connector enablement are manual admin steps.
- Availability of the ONLYOFFICE connector may depend on Nextcloud app-store access.
- This POC does not add automated verification of the Nextcloud-to-MinIO mount.
- This POC does not add conflict resolution, versioning, or document-lock coordination beyond what the integrated products provide.
- Nextcloud is not configured to use MinIO as primary object storage.

## Troubleshooting

- Internal versus browser-facing URLs: use `http://127.0.0.1:${NEXTCLOUD_PORT:-8091}` and `http://127.0.0.1:${ONLYOFFICE_DOCS_PORT:-8090}` in the browser, but use `http://nextcloud/` and `http://onlyoffice-docs/` for container-internal configuration.
- JWT mismatch: if ONLYOFFICE fails to open or save documents, confirm the Nextcloud connector secret exactly matches `${ONLYOFFICE_JWT_SECRET:-change-me-onlyoffice-dev-secret}` used by `onlyoffice-docs`.
- MinIO path-style access: if the S3 mount validates but files do not appear, confirm path-style access is enabled and SSL is disabled for local development.
- External storage mount not showing files: confirm the bucket name is `${ONLYOFFICE_DOCUMENTS_BUCKET:-onlyoffice}`, the host is `minio:9000`, and the credentials match the running MinIO root credentials.
- ONLYOFFICE connector app-store dependency: if the connector app is unavailable, verify outbound app-store access from the Nextcloud environment or install the app manually through supported Nextcloud administration methods.
- Background job / cron warning: the overlay includes `nextcloud-cron`; if Nextcloud still warns about background jobs, verify the `nextcloud-cron` container is running and has access to the shared Nextcloud volumes.
- Redis / file locking warning: if Nextcloud reports transactional file-locking or cache warnings, verify `nextcloud-redis` is running and the `REDIS_HOST` value remains `nextcloud-redis`.
- Accidental root-level file edits: this task must remain confined to `overlay_onlyoffice/`; if changes appear outside that subtree, stop and revert them before proceeding with review.
