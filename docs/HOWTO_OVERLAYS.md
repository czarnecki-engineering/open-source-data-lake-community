# HOWTO_OVERLAYS

## Purpose and Scope

This guide explains how to work with overlays in this repository during development, packaging, installation, and validation.

It is a practical companion to the canonical overlay contract. Use this document for workflow guidance, not as a replacement for the contract.

## Relationship to the Canonical Contract

The canonical contract defines the required overlay rules and compatibility requirements.

Use this guide to apply that contract when creating, testing, packaging, and installing overlays.

Authoritative contract:
- `docs/architecture/overlay_contract_v1.md`

## Overlay Design Principles

Keep overlays additive and isolated from the base runtime.

Prefer overlays that:
- introduce capability without changing base repository behavior
- keep runtime intent clear in overlay-local documentation
- remain easy to install, remove, and validate
- avoid duplicating repository-wide documentation

## Required Overlay File Structure

Follow the canonical contract for required files and layout.

In practice, contributors should expect overlay-specific runtime documentation to live in the packaged overlay directory:
- `overlay_x/overlay_x/README.md`
- `overlay_x/overlay_x/RUNBOOK.md`

## Optional Overlay Documentation

Optional explanatory material may live under:
- `overlay_x/docs/explanation.md`

Compatibility entrypoints may also exist at older paths where needed, but they should redirect readers to the current packaged overlay documentation.

## Local Development Workflow

Develop overlays from the repository root so they can be exercised against the current base runtime.

Typical workflow:
1. make changes inside the overlay source tree
2. start the overlay using its development wrapper when provided
3. inspect Airflow, MinIO, notebooks, and any overlay-specific service output
4. stop the overlay and repeat

Use the overlay-local README and RUNBOOK as the first reference for day-to-day work.

## Testing Workflow

Validate overlays with the smallest practical end-to-end run.

Focus on:
- service startup and clean shutdown
- expected DAG registration and execution
- expected object creation in storage layers
- presence of overlay-delivered notebooks, scripts, and application assets
- absence of unintended impact on the base runtime

Record validation steps in the overlay-local RUNBOOK where future operators will need them.

## Packaging and Archive Creation

Build overlay archives from the overlay source material intended for distribution.

Before publishing an archive:
- confirm the packaged README and RUNBOOK are present
- confirm development-only files are excluded when they are not part of the install artifact
- confirm the archive unpacks cleanly into a compatible repository checkout

Treat archive contents as part of the overlay interface and validate them explicitly.

## Installation Workflow

Install overlays into a compatible repository checkout from the repository root.

After installation:
- follow the packaged overlay README for scope and expectations
- follow the packaged overlay RUNBOOK for execution and validation
- confirm any required local configuration files are created before runtime execution

## Validation Against the Contract

Use the canonical contract as the validation source of truth.

When checking an overlay:
- verify the file structure against the contract
- verify runtime behavior against the overlay-local documentation
- verify installation paths and wrapper scripts behave as documented

## Compatibility Notes

Some legacy documentation paths are retained as compatibility entrypoints.

When both a compatibility entrypoint and a packaged overlay document exist, treat the packaged document as primary.

Do not use compatibility files as the authoritative source when updating overlay guidance.

## Troubleshooting

If an overlay does not behave as expected:
- verify you are using a repository version compatible with the overlay
- verify required local configuration files exist
- verify environment variables are set before startup
- verify the overlay start path matches the intended mode
- verify the overlay-local RUNBOOK steps were followed in order

If the issue remains unclear, inspect the relevant service logs and validate the installed file layout before changing implementation.

## References

- `docs/architecture/overlay_contract_v1.md`
- `docs/releases/v1.1.0-overlay-contract-validation-and-installed-mode-stabilisation.md`
- `RUNBOOK.md`
