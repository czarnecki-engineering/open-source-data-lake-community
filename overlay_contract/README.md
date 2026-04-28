# Generic Overlay Contract

This folder defines the v1 contract for additive Docker Compose overlays on the supported stack.

Use this contract when:

- authoring a new overlay package
- reviewing whether an overlay stays within supported runtime boundaries
- validating that an overlay can run through the root wrapper scripts without modifying the base stack

The reference implementation for this contract lives in `overlay_hello_world/`.

Every publishable overlay should ship packaged runtime docs under `overlay_<name>/README.md` and `overlay_<name>/RUNBOOK.md`.

At minimum, those docs should make these operator paths explicit:

- source-tree dev mode
- archive build
- additive install into a compatible repo root
- installed-runtime startup against the base stack

If an overlay intentionally does not support one of those paths, the docs should say so explicitly rather than leaving the behavior implied.

Start with:

- `MY_FIRST_OVERLAY.md` for the simplest file-only path
- `CONTRACT.md` for the normative rules
- `RUNBOOK.md` for the author workflow
- `APPENDIX_HELLO_WORLD.md` for the minimal worked example
