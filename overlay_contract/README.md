# Generic Overlay Contract

This folder defines the v1 contract for additive Docker Compose overlays on the supported stack.

Use this contract when:

- authoring a new overlay package
- reviewing whether an overlay stays within supported runtime boundaries
- validating that an overlay can run through the root wrapper scripts without modifying the base stack

The reference implementation for this contract lives in `overlay_hello_world/`.

Start with:

- `MY_FIRST_OVERLAY.md` for the simplest file-only path
- `CONTRACT.md` for the normative rules
- `RUNBOOK.md` for the author workflow
- `APPENDIX_HELLO_WORLD.md` for the minimal worked example
