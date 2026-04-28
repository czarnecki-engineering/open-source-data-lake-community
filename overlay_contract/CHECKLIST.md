# Checklist

- The overlay is additive only.
- No protected root file is created or overwritten.
- All overlay-authored payload files are namespaced.
- The overlay targets only logical `airflow`, `jupyter`, and `php`.
- Any Airflow customisation uses only supported logical `airflow` keys.
- The packaged runtime folder exists under `overlay_<name>/`.
- If the overlay has `.env.example`, it is inside the packaged runtime folder.
- Dev-only helpers are not documented as required runtime files.
- The archive command matches `ARCHIVE_RULES.md`.
- File-only overlays validate through additive install plus plain base startup.
- Compose overlays validate through both dev and packaged compose renders.
- Generated runtime outputs are not committed.
- Packaged `README.md` and `RUNBOOK.md` explicitly cover dev mode, archive build, install, and installed-runtime execution.
