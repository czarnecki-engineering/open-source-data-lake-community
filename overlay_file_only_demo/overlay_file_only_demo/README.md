# File Only Demo Overlay

This is the packaged runtime folder for the minimal file-only overlay example.

It intentionally has:

- no overlay compose file
- no overlay start/stop wrapper scripts
- no service-level Docker changes

## Dev / source-tree mode

This overlay has no separate dev wrapper.

Because it is file-only, source-tree development and installed-runtime execution both use the normal base stack commands.

## Build the archive

From the repository root:

```bash
cd overlay_file_only_demo
zip -rq ../overlay_file_only_demo_v1.0.zip php overlay_file_only_demo
```

## Install the overlay

From the root of a compatible Community checkout:

```bash
unzip -oq overlay_file_only_demo_v1.0.zip -d .
```

## Run the installed overlay with the base stack

Install the additive payload into a compatible repo root, then run:

```bash
./start-compose.sh
```

The overlay contributes one untagged PHP solution page:

- `php/solutions/file_only_demo.php`
