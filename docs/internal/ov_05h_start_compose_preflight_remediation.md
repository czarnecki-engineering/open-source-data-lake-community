# OV-05H-R — start-compose.sh Docker Preflight Remediation

## Original Problem
The shared `start-compose.sh` Docker preflight used:

```bash
if ! docker info >/dev/null 2>&1; then
```

That collapsed any `docker info` failure into a generic daemon-down message. In the documented failing wrapper context, the real failure was a Docker socket/context permission error, but the script reported only:

```text
Error: Docker daemon is not running. Start Docker Desktop and try again.
```

This misreported the blocker affecting `overlay_heartbeat_v2` dev-mode, `overlay_heartbeat_v2` installed-mode, and `overlay_kaggle_ingestion` installed-mode.

## Exact Change Made
Updated `start-compose.sh` to keep the Docker preflight while capturing `docker info` combined stdout/stderr:

- store `docker info 2>&1` output in `docker_info_output`
- if the command fails:
  - print `Error: Docker preflight failed.`
  - print the captured Docker error output verbatim
  - print diagnostic hints covering Docker Desktop, Docker context/socket, and Docker socket permission issues
  - exit non-zero

Successful startup behavior remains unchanged because the script still requires `docker info` to succeed before continuing.

## Validation Commands Run
```bash
bash -n start-compose.sh
./start-compose.sh
bash overlay_heartbeat_v2/dev-start-compose.sh
```

The remaining runtime commands from the validation plan were not run because both startup paths failed at the Docker preflight and no stack was started.

## Base Startup Result
- `bash -n start-compose.sh`: passed
- `./start-compose.sh`: failed at Docker preflight
- surfaced Docker error:

```text
Server:
failed to connect to the docker API at unix:///Users/marekczarnecki/.docker/run/docker.sock; check if the path is correct and if the daemon is running: dial unix /Users/marekczarnecki/.docker/run/docker.sock: connect: no such file or directory
```

- result: accurate failure message shown; no false “Docker daemon is not running” only message

## Heartbeat Startup Result
- `bash overlay_heartbeat_v2/dev-start-compose.sh`: failed at the same Docker preflight
- surfaced Docker error:

```text
Server:
failed to connect to the docker API at unix:///Users/marekczarnecki/.docker/run/docker.sock; check if the path is correct and if the daemon is running: dial unix /Users/marekczarnecki/.docker/run/docker.sock: connect: no such file or directory
```

- result: accurate failure message shown through the heartbeat wrapper; runtime did not start, so Compose `ps`, DAG visibility, and stop commands were not applicable in this run

## Accuracy of Error Message After Remediation
Yes. The preflight now reports the actual `docker info` failure output instead of always claiming Docker is not running. This addresses socket/context/permission failures being misclassified as daemon-down failures.

## Remaining Issues
- The underlying Docker client/server connection issue remains in this shell context: `docker info` is targeting `unix:///Users/marekczarnecki/.docker/run/docker.sock` and receives `connect: no such file or directory`.
- Installed-mode heartbeat and Kaggle validations should be rerun after the Docker environment/context issue is corrected, using this remediated preflight output for diagnosis.
