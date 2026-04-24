# File Only Demo Overlay

This is the packaged runtime folder for the minimal file-only overlay example.

It intentionally has:

- no overlay compose file
- no overlay start/stop wrapper scripts
- no service-level Docker changes

Install the additive payload into a compatible repo root, then run:

```bash
./start-compose.sh
```

The overlay contributes one untagged PHP solution page:

- `php/solutions/file_only_demo.php`
