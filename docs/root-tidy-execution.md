# Root Tidy Execution

## Files moved
- `CONTENTS.md` -> `docs/reference/CONTENTS.md`
- `IMPLEMENTED_CAPABILITIES.md` -> `docs/reference/IMPLEMENTED_CAPABILITIES.md`
- `PROJECT_CONTEXT.md` -> `docs/internal/PROJECT_CONTEXT.md`
- `TODO.md` -> `docs/internal/TODO.md`

## Files updated (links)
- `README.md`
- `docs/reference/CONTENTS.md`
- `docs/internal/TODO.md`
- `docs/community-compose-alignment-execution.md`
- `docs/root-tidy-discovery.md`

## Files deleted
- `.gitignore copy`

## Root layout after change
```text
.
├── .env.example
├── README.md
├── RUNBOOK.md
├── config/
├── dags/
├── docker/
├── docker-compose.yaml
├── docs/
│   ├── internal/
│   ├── reference/
│   └── ...
├── logs/
├── notebooks/
├── open-source-data-lake-community.code-workspace
├── php/
├── plugins/
├── start-compose.sh
└── stop-compose.sh
```

## Notes
- No runtime files, compose wiring, scripts, entrypoints, or mounted directories were changed.
- `docker-compose.yaml`, `start-compose.sh`, `stop-compose.sh`, `README.md`, `RUNBOOK.md`, `config/`, `dags/`, `docker/`, `logs/`, `notebooks/`, `php/`, `plugins/`, and `.env.example` remain at repo root.
