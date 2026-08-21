# Open Source Data Lake Team

This repository is the working repository for the Open Source Data Lake Team runtime and architecture work.

## Purpose

- Hold the current working runtime, architecture memory, ADRs, handoff notes, and implementation sequencing.
- Provide one place to rationalise the Foundation baseline, Team runtime direction, and future Compose/Kubernetes alignment.
- Preserve a stable working reference for ChatGPT, Codex, and local development sessions.

## Current Status

- This repository currently carries forward the Knowledge Lake rebuild structure as the starting point for Team work.
- The handoff documents (capability matrix, next actions) and the ADRs are the source-of-truth inputs — see below.
- Both the local Kubernetes path (`runtime/knowledge-lake/`) and the Docker Compose path (`runtime/foundation/compose/`) are validated, working runtimes as of 2026-08-20, sharing the same `runtime/shared/` mount tree and `runtime/shared/.env` config. They default to the same localhost ports and cannot run simultaneously.

## Relationship To Foundation And Team Runtime Work

- Foundation remains the baseline runtime reference.
- This Team repository is the working place for reducing, reorganising, and stabilising the runtime shape.
- Current direction is to simplify the service set where possible and align Kubernetes and Compose around the same repo-visible mount structure.

## Documentation

**[`docs/README.md`](docs/README.md) is the full documentation index — start there for anything not listed below.**

Quickest entry points:

- [Runtime Capability Matrix](docs/handoff/runtime-capability-matrix.md) — what's accepted, unproven, deferred. Start here for project status.
- Runtime guides — pick one stack, they share ports and can't both run at once: [Kubernetes](runtime/knowledge-lake/README.md) · [Docker Compose](runtime/foundation/compose/README.md).

## How To Use This Repo

1. Start with [`docs/README.md`](docs/README.md), or directly with the [Runtime Capability Matrix](docs/handoff/runtime-capability-matrix.md) and [Next Actions](docs/handoff/next-actions.md).
2. Use [architecture context](docs/architecture/context.md), [principles](docs/architecture/principles.md), and [glossary](docs/architecture/glossary.md) as the shared working baseline.
3. Record locked decisions in `docs/architecture/decisions/` before treating them as final.
4. For the current local runtime workflow, pick one stack: [Kubernetes guide](runtime/knowledge-lake/README.md) + [`TROUBLESHOOTING.md`](docs/runtime/knowledge-lake/TROUBLESHOOTING.md), or [Compose guide](runtime/foundation/compose/README.md) + [`TROUBLESHOOTING.md`](docs/runtime/compose/TROUBLESHOOTING.md).

## Working Direction

- Keep runtime mounts repo-visible and easy to reason about.
- Prefer one shared authored mount tree under `runtime/shared/` for both Kubernetes and future Compose work where practical.
- Reduce unnecessary service breadth rather than expanding every runtime mode to the largest current stack.
- Preserve Foundation compatibility unless an ADR explicitly changes direction.

## Warning

This repository is now a working Team repo, but much of the current structure was copied from the Knowledge Lake rebuild and should be treated as inherited starting state rather than final Team packaging.
