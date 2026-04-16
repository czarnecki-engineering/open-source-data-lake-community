# Environment Configuration Discovery
- Repo: open-source-data-lake-community
- Mode: Read-only discovery
- Generated: 2026-04-16 21:23:01 AEST

## A. Variables Used in docker-compose.yaml

`docker-compose.yaml` uses `${VAR:-default}` syntax for all variable interpolation found in the file. No `${VAR}` entries without defaults were found in `docker-compose.yaml`. Evidence: [docker-compose.yaml:9](./docker-compose.yaml#L9), [docker-compose.yaml:10](./docker-compose.yaml#L10), [docker-compose.yaml:12](./docker-compose.yaml#L12), [docker-compose.yaml:13](./docker-compose.yaml#L13), [docker-compose.yaml:32](./docker-compose.yaml#L32), [docker-compose.yaml:63](./docker-compose.yaml#L63), [docker-compose.yaml:64](./docker-compose.yaml#L64), [docker-compose.yaml:68](./docker-compose.yaml#L68), [docker-compose.yaml:71](./docker-compose.yaml#L71), [docker-compose.yaml:74](./docker-compose.yaml#L74), [docker-compose.yaml:77](./docker-compose.yaml#L77), [docker-compose.yaml:88](./docker-compose.yaml#L88), [docker-compose.yaml:105](./docker-compose.yaml#L105), [docker-compose.yaml:107](./docker-compose.yaml#L107), [docker-compose.yaml:116](./docker-compose.yaml#L116), [docker-compose.yaml:122](./docker-compose.yaml#L122).

| Variable | Default | Where used |
| --- | --- | --- |
| `MINIO_API_PORT` | `9000` | MinIO published port mapping. Evidence: [docker-compose.yaml:9](./docker-compose.yaml#L9) |
| `MINIO_CONSOLE_PORT` | `9001` | MinIO Console published port mapping. Evidence: [docker-compose.yaml:10](./docker-compose.yaml#L10) |
| `MINIO_ROOT_USER` | `minioadmin` | MinIO env `MINIO_ROOT_USER`; MinIO init `mc alias set`; Airflow env `AWS_ACCESS_KEY_ID`. Evidence: [docker-compose.yaml:12](./docker-compose.yaml#L12), [docker-compose.yaml:32](./docker-compose.yaml#L32), [docker-compose.yaml:63](./docker-compose.yaml#L63) |
| `MINIO_ROOT_PASSWORD` | `minioadmin` | MinIO env `MINIO_ROOT_PASSWORD`; MinIO init `mc alias set`; Airflow env `AWS_SECRET_ACCESS_KEY`. Evidence: [docker-compose.yaml:13](./docker-compose.yaml#L13), [docker-compose.yaml:32](./docker-compose.yaml#L32), [docker-compose.yaml:64](./docker-compose.yaml#L64) |
| `AIRFLOW_UID` | `50000` | Airflow env `AIRFLOW_UID`. Evidence: [docker-compose.yaml:68](./docker-compose.yaml#L68) |
| `AIRFLOW_PIP_ADDITIONAL_REQUIREMENTS` | `yfinance pyarrow pandas` | Airflow env `PIP_ADDITIONAL_REQUIREMENTS`. Evidence: [docker-compose.yaml:71](./docker-compose.yaml#L71) |
| `AIRFLOW_VAR_ASX_TICKERS` | `BHP,CBA,CSL,RIO,WES` | Airflow env `AIRFLOW_VAR_ASX_TICKERS`. Evidence: [docker-compose.yaml:74](./docker-compose.yaml#L74) |
| `AIRFLOW_PORT` | `8080` | Airflow published port mapping. Evidence: [docker-compose.yaml:77](./docker-compose.yaml#L77) |
| `AIRFLOW_ADMIN_USERNAME` | `minioadmin` | Airflow startup command `airflow users create --username ...`. Evidence: [docker-compose.yaml:88](./docker-compose.yaml#L88) |
| `AIRFLOW_ADMIN_PASSWORD` | `minioadmin` | Airflow startup command `airflow users create --password ...`. Evidence: [docker-compose.yaml:88](./docker-compose.yaml#L88) |
| `AIRFLOW_ADMIN_EMAIL` | `admin@example.com` | Airflow startup command `airflow users create --email ...`. Evidence: [docker-compose.yaml:88](./docker-compose.yaml#L88) |
| `JUPYTER_PORT` | `8888` | Jupyter published port mapping. Evidence: [docker-compose.yaml:105](./docker-compose.yaml#L105) |
| `JUPYTER_TOKEN` | `jupyter` | Jupyter env `JUPYTER_TOKEN`. Evidence: [docker-compose.yaml:107](./docker-compose.yaml#L107) |
| `PHP_PORT` | `8088` | PHP published port mapping. Evidence: [docker-compose.yaml:116](./docker-compose.yaml#L116) |
| `TZ` | `Australia/Melbourne` | PHP env `TZ`. Evidence: [docker-compose.yaml:122](./docker-compose.yaml#L122) |

There are also hardcoded, non-interpolated values in `docker-compose.yaml` that are configuration but are not controlled by `.env.example`, including `S3_ENDPOINT_URL=http://minio:9000`, `AWS_DEFAULT_REGION=us-east-1`, `AIRFLOW__CORE__EXECUTOR=SequentialExecutor`, `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=sqlite:////opt/airflow/airflow.db`, `AIRFLOW__CORE__LOAD_EXAMPLES=False`, `AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=False`, `AIRFLOW__WEBSERVER__EXPOSE_CONFIG=True`, and `SERVER_NAME=:80`. Evidence: [docker-compose.yaml:55](./docker-compose.yaml#L55)-[65](./docker-compose.yaml#L65), [docker-compose.yaml:121](./docker-compose.yaml#L121).

## B. `.env` Usage (Actual Behaviour)

Explicit `.env` loading by repo scripts: `NO`.

- `start-compose.sh` does not run `source .env`, `. .env`, `export ...`, or `docker compose --env-file ...`; it runs plain `docker compose build` and `docker compose up -d`. Evidence: [start-compose.sh:35](./start-compose.sh#L35)-[39](./start-compose.sh#L39).
- `stop-compose.sh` also does not reference `.env`; it runs plain `docker compose down` or `docker compose down -v`. Evidence: [stop-compose.sh:43](./stop-compose.sh#L43)-[48](./stop-compose.sh#L48).
- No `env_file:` directive exists in `docker-compose.yaml`. Evidence: [docker-compose.yaml:1](./docker-compose.yaml#L1)-[127](./docker-compose.yaml#L127).

Implicit `.env` use by `docker compose`: `PARTIALLY EVIDENCED`.

- `start-compose.sh` prints: `Default access URLs (may differ if overridden via .env)`, which is repo evidence that the script expects `.env`-based overrides to affect Compose startup. Evidence: [start-compose.sh:46](./start-compose.sh#L46)-[51](./start-compose.sh#L51).
- A repo document under `docs/source/` states `.env auto-loaded — supported in your version`. Evidence: [docs/source/chat-airflow.md:608](./docs/source/chat-airflow.md#L608)-[610](./docs/source/chat-airflow.md#L610).
- Authoritative startup code does not itself prove Docker Compose precedence rules; the repo contains no code path that explicitly loads `.env`. Relative precedence between shell environment and implicit `.env` is therefore `NOT VERIFIED` from authoritative startup code alone.

## C. `.env.example` Coverage

Coverage against interpolated variables in `docker-compose.yaml`: `YES`.

- Every interpolated variable found in `docker-compose.yaml` appears in `.env.example`: `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_API_PORT`, `MINIO_CONSOLE_PORT`, `AIRFLOW_ADMIN_USERNAME`, `AIRFLOW_ADMIN_PASSWORD`, `AIRFLOW_ADMIN_EMAIL`, `AIRFLOW_PORT`, `AIRFLOW_UID`, `AIRFLOW_VAR_ASX_TICKERS`, `AIRFLOW_PIP_ADDITIONAL_REQUIREMENTS`, `JUPYTER_TOKEN`, `JUPYTER_PORT`, `PHP_PORT`, `TZ`. Evidence: [docker-compose.yaml:9](./docker-compose.yaml#L9)-[13](./docker-compose.yaml#L13), [docker-compose.yaml:32](./docker-compose.yaml#L32), [docker-compose.yaml:63](./docker-compose.yaml#L63)-[64](./docker-compose.yaml#L64), [docker-compose.yaml:68](./docker-compose.yaml#L68), [docker-compose.yaml:71](./docker-compose.yaml#L71), [docker-compose.yaml:74](./docker-compose.yaml#L74), [docker-compose.yaml:77](./docker-compose.yaml#L77), [docker-compose.yaml:88](./docker-compose.yaml#L88), [docker-compose.yaml:105](./docker-compose.yaml#L105), [docker-compose.yaml:107](./docker-compose.yaml#L107), [docker-compose.yaml:116](./docker-compose.yaml#L116), [docker-compose.yaml:122](./docker-compose.yaml#L122); [\.env.example:2](./.env.example#L2)-[22](./.env.example#L22).
- Variables in compose not present in `.env.example`: `NONE` for interpolated variables.
- Variables in `.env.example` not used in `docker-compose.yaml` interpolation: `NONE`.

`.env.example` references in requested docs/scripts:

- `README.md`: no `.env.example` reference found in repo search. `NOT VERIFIED` by direct file text because absence cannot be line-cited; repo search over `README.md` returned no `.env.example` match.
- `RUNBOOK.md`: no `.env.example` reference found in repo search. `NOT VERIFIED` by direct file text because absence cannot be line-cited; repo search over `RUNBOOK.md` returned no `.env.example` match.
- `start-compose.sh`: no `.env.example` reference. Evidence: [start-compose.sh:1](./start-compose.sh#L1)-[52](./start-compose.sh#L52).
- `stop-compose.sh`: no `.env.example` reference. Evidence: [stop-compose.sh:1](./stop-compose.sh#L1)-[49](./stop-compose.sh#L49).
- Other docs do reference `.env.example`, for example `docs/community-compose-alignment-execution.md` says `.env.example` was edited and aligned with `docker-compose.yaml`, and `docs/root-tidy-discovery.md` says it is not consumed through `env_file:`. Evidence: [docs/community-compose-alignment-execution.md:7](./docs/community-compose-alignment-execution.md#L7)-[12](./docs/community-compose-alignment-execution.md#L12), [docs/root-tidy-discovery.md:56](./docs/root-tidy-discovery.md#L56), [docs/root-tidy-discovery.md:148](./docs/root-tidy-discovery.md#L148)-[149](./docs/root-tidy-discovery.md#L149).

## D. Startup Script Behaviour

`start-compose.sh` behaviour:

- It enforces running from the repo root by comparing the current directory to the script directory and by checking for `docker-compose.yaml`. Evidence: [start-compose.sh:4](./start-compose.sh#L4)-[17](./start-compose.sh#L17).
- It checks that `docker`, the Docker daemon, and `docker compose` v2 are available. Evidence: [start-compose.sh:20](./start-compose.sh#L20)-[33](./start-compose.sh#L33).
- It runs exactly:
  - `docker compose build`
  - `docker compose up -d`
  - `sleep 5`
  Evidence: [start-compose.sh:35](./start-compose.sh#L35)-[42](./start-compose.sh#L42).
- It does not reference `.env.example`. Evidence: [start-compose.sh:1](./start-compose.sh#L1)-[52](./start-compose.sh#L52).
- It does not reference `.env` except in a printed note about possible overrides. Evidence: [start-compose.sh:46](./start-compose.sh#L46)-[51](./start-compose.sh#L51).
- It does not `export` variables or otherwise modify the shell environment. Evidence: [start-compose.sh:1](./start-compose.sh#L52).
- Based on the code path, it relies on `docker compose` to perform any variable interpolation and default handling. Evidence: [start-compose.sh:35](./start-compose.sh#L39), [docker-compose.yaml:9](./docker-compose.yaml#L9)-[13](./docker-compose.yaml#L13), [docker-compose.yaml:68](./docker-compose.yaml#L68), [docker-compose.yaml:71](./docker-compose.yaml#L71), [docker-compose.yaml:74](./docker-compose.yaml#L74), [docker-compose.yaml:77](./docker-compose.yaml#L77), [docker-compose.yaml:88](./docker-compose.yaml#L88), [docker-compose.yaml:105](./docker-compose.yaml#L105), [docker-compose.yaml:107](./docker-compose.yaml#L107), [docker-compose.yaml:116](./docker-compose.yaml#L116), [docker-compose.yaml:122](./docker-compose.yaml#L122).

## E. Configuration Precedence

Evidence-based precedence from this repo:

1. Value resolved by `docker compose` for `${VAR:-default}` before the Compose model is applied.
   Evidence: all interpolated entries use `${VAR:-default}` in `docker-compose.yaml`. Examples: [docker-compose.yaml:12](./docker-compose.yaml#L12), [docker-compose.yaml:68](./docker-compose.yaml#L68), [docker-compose.yaml:77](./docker-compose.yaml#L77), [docker-compose.yaml:107](./docker-compose.yaml#L107).
2. If no external value is resolved, the fallback inside `docker-compose.yaml` is used.
   Evidence: same lines as above.
3. For settings without interpolation, the hardcoded literal in `docker-compose.yaml` is used.
   Evidence: [docker-compose.yaml:55](./docker-compose.yaml#L55)-[65](./docker-compose.yaml#L65), [docker-compose.yaml:121](./docker-compose.yaml#L121).

For a variable such as `MINIO_ROOT_USER`, the repo proves this much:

- External value supplied to Compose resolution: used if Compose resolves one. Whether shell environment beats implicit `.env`, or vice versa, is `NOT VERIFIED` from authoritative startup code in this repo.
- Otherwise Compose fallback default applies: `minioadmin`. Evidence: [docker-compose.yaml:12](./docker-compose.yaml#L12), [docker-compose.yaml:32](./docker-compose.yaml#L32), [docker-compose.yaml:63](./docker-compose.yaml#L63).
- There is no separate hardcoded post-resolution override in `start-compose.sh` or `stop-compose.sh`. Evidence: [start-compose.sh:35](./start-compose.sh#L35)-[39](./start-compose.sh#L39), [stop-compose.sh:43](./stop-compose.sh#L43)-[48](./stop-compose.sh#L48).

`.env.example` is not part of runtime precedence. It is a template file only; no script or compose directive consumes it directly. Evidence: [start-compose.sh:1](./start-compose.sh#L1)-[52](./start-compose.sh#L52), [stop-compose.sh:1](./stop-compose.sh#L1)-[49](./stop-compose.sh#L49), [docker-compose.yaml:1](./docker-compose.yaml#L1)-[127](./docker-compose.yaml#L127), [docs/root-tidy-discovery.md:56](./docs/root-tidy-discovery.md#L56).

## F. Current Default Behaviour (No `.env`)

If a user runs `./start-compose.sh` without creating `.env`, the startup script still runs `docker compose build` and `docker compose up -d`. Evidence: [start-compose.sh:35](./start-compose.sh#L39).

Configuration values that will be used by default come from `docker-compose.yaml` fallbacks and hardcoded literals:

- MinIO API port `9000`; MinIO Console port `9001`; MinIO credentials `minioadmin` / `minioadmin`. Evidence: [docker-compose.yaml:9](./docker-compose.yaml#L9)-[13](./docker-compose.yaml#L13).
- Airflow port `8080`; admin username `minioadmin`; admin password `minioadmin`; admin email `admin@example.com`; `AIRFLOW_UID=50000`; `PIP_ADDITIONAL_REQUIREMENTS=yfinance pyarrow pandas`; `AIRFLOW_VAR_ASX_TICKERS=BHP,CBA,CSL,RIO,WES`. Evidence: [docker-compose.yaml:68](./docker-compose.yaml#L68), [docker-compose.yaml:71](./docker-compose.yaml#L71), [docker-compose.yaml:74](./docker-compose.yaml#L74), [docker-compose.yaml:77](./docker-compose.yaml#L77), [docker-compose.yaml:88](./docker-compose.yaml#L88).
- Jupyter port `8888`; token `jupyter`. Evidence: [docker-compose.yaml:105](./docker-compose.yaml#L105)-[107](./docker-compose.yaml#L107).
- PHP port `8088`; `TZ=Australia/Melbourne`. Evidence: [docker-compose.yaml:116](./docker-compose.yaml#L116), [docker-compose.yaml:122](./docker-compose.yaml#L122).
- Hardcoded service config also applies: `S3_ENDPOINT_URL=http://minio:9000`, `AWS_DEFAULT_REGION=us-east-1`, Airflow `SequentialExecutor`, SQLite metadata DB path, and PHP `SERVER_NAME=:80`. Evidence: [docker-compose.yaml:55](./docker-compose.yaml#L55)-[65](./docker-compose.yaml#L65), [docker-compose.yaml:121](./docker-compose.yaml#L121).

Will the system still work without `.env`?

- The repo documentation presents default URLs and credentials as the expected normal startup outcome. Evidence: [README.md:94](./README.md#L94)-[101](./README.md#L101), [RUNBOOK.md:45](./RUNBOOK.md#L45)-[57](./RUNBOOK.md#L57), [start-compose.sh:46](./start-compose.sh#L46)-[51](./start-compose.sh#L51).
- The ASX ingestion DAG has a separate manual requirement: `config/asx200_tickers.csv` must be created manually, and if it is missing the DAG will fail. Evidence: [README.md:21](./README.md#L21), [README.md:81](./README.md#L81)-[92](./README.md#L92).
- The same README says platform health is based on services starting, Airflow UI accessibility, and heartbeat DAGs running; absence of ASX data does not indicate platform failure. Evidence: [README.md:88](./README.md#L88)-[92](./README.md#L92), [README.md:105](./README.md#L105)-[113](./README.md#L113).

Therefore, on repo evidence alone: the stack is intended to start and use compose defaults without `.env`, but full ASX pipeline operation still depends on the separate `config/asx200_tickers.csv` file. For a fresh clone with no manual file creation, successful service startup is evidenced as intended; complete ASX DAG success is not. Fresh-clone presence of `config/asx200_tickers.csv` is `NOT VERIFIED` from tracked repository contents alone.

## G. User Confusion / Risks

- `.env.example` looks like a runtime input, but the repo does not wire it via `env_file:` and no script copies or sources it. Users must infer that they need an actual `.env` or shell environment values. Evidence: [docker-compose.yaml:1](./docker-compose.yaml#L127), [start-compose.sh:35](./start-compose.sh#L39), [docs/root-tidy-discovery.md:56](./docs/root-tidy-discovery.md#L56).
- `start-compose.sh` mentions `.env`, but `README.md` and `RUNBOOK.md` do not tell the user to create `.env` or copy `.env.example`. Evidence: [start-compose.sh:46](./start-compose.sh#L46), [README.md:18](./README.md#L18)-[46](./README.md#L46), [RUNBOOK.md:41](./RUNBOOK.md#L41)-[57](./RUNBOOK.md#L57).
- Some important service settings are hardcoded and are not exposed through `.env.example`, for example `S3_ENDPOINT_URL`, `AWS_DEFAULT_REGION`, Airflow executor/database/webserver flags, and PHP `SERVER_NAME`. These settings appear configurable only by editing `docker-compose.yaml`. Evidence: [docker-compose.yaml:55](./docker-compose.yaml#L65), [docker-compose.yaml:121](./docker-compose.yaml#L121).
- The startup script prints fixed default URLs after startup and does not compute actual effective ports from the resolved environment. If ports are overridden, the printed URLs may be stale. Evidence: [start-compose.sh:44](./start-compose.sh#L44)-[51](./start-compose.sh#L51), [docker-compose.yaml:9](./docker-compose.yaml#L9)-[10](./docker-compose.yaml#L10), [docker-compose.yaml:77](./docker-compose.yaml#L77), [docker-compose.yaml:105](./docker-compose.yaml#L105), [docker-compose.yaml:116](./docker-compose.yaml#L116).
- `README.md` instructs the operator to create `config/asx200_tickers.csv`, but that requirement is separate from `.env` and can be missed when evaluating whether startup “worked”. Evidence: [README.md:21](./README.md#L21), [README.md:81](./README.md#L81)-[92](./README.md#L92).

## H. Required User Actions (Current State)

To change ports:

- Set the relevant Compose variables before running `./start-compose.sh`, using values resolved by `docker compose` for `MINIO_API_PORT`, `MINIO_CONSOLE_PORT`, `AIRFLOW_PORT`, `JUPYTER_PORT`, and `PHP_PORT`. Evidence: [docker-compose.yaml:9](./docker-compose.yaml#L9)-[10](./docker-compose.yaml#L10), [docker-compose.yaml:77](./docker-compose.yaml#L77), [docker-compose.yaml:105](./docker-compose.yaml#L105), [docker-compose.yaml:116](./docker-compose.yaml#L116), [start-compose.sh:35](./start-compose.sh#L35)-[39](./start-compose.sh#L39).
- The repo suggests `.env` can be one such override source, but no script creates it. Evidence: [start-compose.sh:46](./start-compose.sh#L46)-[51](./start-compose.sh#L51).
- `.env.example` is only a template and is not consumed directly. Evidence: [docs/root-tidy-discovery.md:56](./docs/root-tidy-discovery.md#L56).

To change credentials:

- Set `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `AIRFLOW_ADMIN_USERNAME`, `AIRFLOW_ADMIN_PASSWORD`, `AIRFLOW_ADMIN_EMAIL`, and `JUPYTER_TOKEN` before startup using Compose-resolved variables. Evidence: [docker-compose.yaml:12](./docker-compose.yaml#L12)-[13](./docker-compose.yaml#L13), [docker-compose.yaml:63](./docker-compose.yaml#L63)-[64](./docker-compose.yaml#L64), [docker-compose.yaml:88](./docker-compose.yaml#L88), [docker-compose.yaml:107](./docker-compose.yaml#L107).
- Changing `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` also changes the Airflow container’s `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` because those values are derived from the same variables. Evidence: [docker-compose.yaml:63](./docker-compose.yaml#L63)-[64](./docker-compose.yaml#L64).

To change service config:

- For settings already exposed as interpolated variables, set those variables before startup: `AIRFLOW_UID`, `AIRFLOW_PIP_ADDITIONAL_REQUIREMENTS`, `AIRFLOW_VAR_ASX_TICKERS`, and `TZ`. Evidence: [docker-compose.yaml:68](./docker-compose.yaml#L68), [docker-compose.yaml:71](./docker-compose.yaml#L71), [docker-compose.yaml:74](./docker-compose.yaml#L74), [docker-compose.yaml:122](./docker-compose.yaml#L122).
- For settings hardcoded in `docker-compose.yaml` and not exposed as interpolated variables, the repo evidence shows no safer override mechanism than editing `docker-compose.yaml` itself. Examples: `S3_ENDPOINT_URL`, `AWS_DEFAULT_REGION`, Airflow executor/database/webserver settings, and PHP `SERVER_NAME`. Evidence: [docker-compose.yaml:55](./docker-compose.yaml#L65), [docker-compose.yaml:121](./docker-compose.yaml#L121).
- For ASX pipeline input configuration, the user must create or edit `config/asx200_tickers.csv`; this is outside `.env` handling. Evidence: [README.md:21](./README.md#L21), [README.md:81](./README.md#L92), [docker-compose.yaml:82](./docker-compose.yaml#L82).

Safe override method from repo evidence:

- Prepare values before running `docker compose build` / `docker compose up -d` through the Compose variable resolution path used by `start-compose.sh`. Whether that is via shell environment or implicit `.env` exists in repo evidence, but the exact precedence between those two sources is `NOT VERIFIED` from authoritative startup code in this repo. Evidence: [start-compose.sh:35](./start-compose.sh#L35)-[39](./start-compose.sh#L39), [start-compose.sh:46](./start-compose.sh#L46), [docs/source/chat-airflow.md:610](./docs/source/chat-airflow.md#L610).

## I. Gaps in Documentation

- `README.md` and `RUNBOOK.md` do not document the existence or use of `.env.example`, and they do not instruct the user to create `.env` before startup. Evidence: [README.md:18](./README.md#L18)-[46](./README.md#L46), [RUNBOOK.md:41](./RUNBOOK.md#L41)-[57](./RUNBOOK.md#L57).
- `README.md` and `RUNBOOK.md` document default service URLs and wrapper commands, but they do not document which specific variables can be overridden. Evidence: [README.md:94](./README.md#L94)-[99](./README.md#L99), [RUNBOOK.md:51](./RUNBOOK.md#L57).
- `start-compose.sh` hints at `.env` overrides, but the canonical docs do not explain how `.env.example` relates to `.env`. Evidence: [start-compose.sh:46](./start-compose.sh#L46), [README.md:18](./README.md#L18)-[46](./README.md#L46), [RUNBOOK.md:41](./RUNBOOK.md#L41)-[57](./RUNBOOK.md#L57).
- The canonical docs do not distinguish clearly between configuration controlled by Compose variables and configuration hardcoded in `docker-compose.yaml`. Evidence: [docker-compose.yaml:55](./docker-compose.yaml#L65), [docker-compose.yaml:121](./docker-compose.yaml#L121), [README.md:94](./README.md#L94)-[99](./README.md#L99), [RUNBOOK.md:51](./RUNBOOK.md#L57).
