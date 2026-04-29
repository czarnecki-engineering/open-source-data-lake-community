# OV-05H — Heartbeat Startup Diagnosis

## Summary
`overlay_heartbeat_v2/dev-start-compose.sh` is not failing because Docker Desktop is down. The failure occurs because the wrapper delegates into `start-compose.sh`, which runs `docker info` inside a non-login Bash script context. In this environment, `docker info` exits `1` with `permission denied while trying to connect to the docker API at unix:///Users/marekczarnecki/.docker/run/docker.sock`, even though `docker info` succeeds in the direct shell. `start-compose.sh` collapses that non-zero exit into the generic message `Error: Docker daemon is not running`, which is a false negative.

## Comparison of Wrappers
- `overlay_heartbeat_v2/dev-start-compose.sh`:
  - computes `repo_root` from `BASH_SOURCE`
  - `exec`s `${repo_root}/start-compose.sh --overlay overlay_heartbeat_v2/dev-docker-compose.overlay-heartbeat-v2.yaml`
- `overlay_asx_historic_csv/dev-start-compose.sh`:
  - same structure as heartbeat, with only the overlay YAML path changed
- `overlay_kaggle_ingestion/dev-start-compose.sh`:
  - same structure as heartbeat, with only the overlay YAML path changed
- `overlay_hello_world/dev-start-compose.sh`:
  - checks that the current directory is the repo root
  - `exec`s `bash "${repo_root}/start-compose.sh" --overlay ...`
- None of the wrappers:
  - modify `PATH`
  - export Docker-specific environment variables
  - run `cd` before invoking `start-compose.sh`
  - invoke `sh`
- Conclusion:
  - heartbeat does not contain a unique wrapper bug relative to ASX/Kaggle
  - the failure point is the shared `start-compose.sh` Docker check, not heartbeat-specific wrapper logic

## Docker Check Analysis
- Direct shell:
  - command: `docker info`
  - result: success, exit code `0`
- Subshell:
  - command: `bash -c 'docker info; printf "EXIT:%s\n" "$?"'`
  - result: failure, exit code `1`
  - stderr: `permission denied while trying to connect to the docker API at unix:///Users/marekczarnecki/.docker/run/docker.sock`
- Wrapper context:
  - command: `bash overlay_heartbeat_v2/dev-start-compose.sh`
  - result: failure, exit code `1`
  - stderr:
    - `Resolved overlays (merge order):`
    - `- overlay_heartbeat_v2/dev-docker-compose.overlay-heartbeat-v2.yaml`
    - `Error: Docker daemon is not running. Start Docker Desktop and try again.`
- Interpretation:
  - the direct shell and the wrapper are not using an equivalent Docker client context
  - the wrapper reaches a Bash script context where `docker info` cannot access the Docker socket and returns non-zero
  - `start-compose.sh` interprets any non-zero exit from `docker info` as “daemon not running,” even when the real error is socket permission/context access

## Root Cause
The false block is caused by the shared `start-compose.sh` check `if ! docker info >/dev/null 2>&1; then`, which runs inside a non-login Bash script context where `docker info` fails with a Docker socket permission/context error; that failure is then misclassified as “Docker daemon is not running.”

## Classification
shell

## Exact Failing Condition
- file: [start-compose.sh](/Users/marekczarnecki/Documents/GitHub/open-source-data-lake-community/start-compose.sh:251)
- line: `251`
- condition: `if ! docker info >/dev/null 2>&1; then`

## Recommended Fix Approach (DO NOT IMPLEMENT)
Keep the Docker preflight in `start-compose.sh`, but make it distinguish “docker command cannot reach the selected socket/context” from “daemon is not running.” The minimal remediation is to capture and surface the real `docker info` stderr or to probe the Docker context/socket in the same shell mode the wrapper uses instead of emitting a generic daemon-down message.

## Next Task Recommendation
- OV-05H-R — Remediate heartbeat wrapper
