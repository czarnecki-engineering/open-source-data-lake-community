# Install Rules

Overlays install into an existing compatible base checkout.

Install safety rules:

- unzip additively into the target repo root
- do not overwrite protected root files
- do not replace unrelated existing files under `config/`, `scripts/`, `dags/`, `notebooks/`, `php/solutions/`, or `data/`
- keep overlay payload namespaced so additive unzip remains safe
- overlay compose files are optional
- packaged overlay start/stop wrappers are optional for file-only overlays

Protected root files:

- `./start-compose.sh`
- `./stop-compose.sh`
- `./docker-compose.yaml`
- `./.env`
- `./README.md`
- `./RUNBOOK.md`

After install, operators may copy example config files into runnable config files when the overlay specifically documents that step.

Activation model after install:

- file-only overlays become available through the base stack's normal mounts and do not require `--overlay`
- compose overlays require explicit root-wrapper activation through one or more `--overlay <compose-file-or-name>` arguments
