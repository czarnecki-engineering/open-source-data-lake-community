# OV-05H-D — Docker Context Fix

## Root Cause
The active Docker CLI context was already correct:

- context: `desktop-linux`
- configured endpoint: `unix:///Users/marekczarnecki/.docker/run/docker.sock`
- `DOCKER_HOST`: unset

The failure was not caused by a stale `DOCKER_HOST` or the wrong Docker context. The real problem was that Docker Desktop was not running, so the configured socket path did not exist yet. Once Docker Desktop started, the expected socket appeared at `~/.docker/run/docker.sock` and both `docker info` and `bash -c "docker info"` succeeded against the same `desktop-linux` context.

## Before State
- context: `desktop-linux`
- `DOCKER_HOST`: unset
- socket: `unix:///Users/marekczarnecki/.docker/run/docker.sock`
- filesystem state before fix:
  - `~/.docker/run/` existed but contained no `docker.sock`
  - `/var/run/docker.sock` was a symlink to `/Users/marekczarnecki/.docker/run/docker.sock`
- `docker info`: failed with `connect: no such file or directory`

## Fix Applied
Exact commands run:

```bash
docker context ls
docker context show
docker context inspect --format '{{ .Endpoints.docker.Host }}'
echo "$DOCKER_HOST"
env | grep DOCKER
ls -la ~/.docker/run/
ls -la /var/run/docker.sock
docker info
docker context inspect desktop-linux
open -a Docker
sleep 20
ls -la ~/.docker/run/
docker info
bash -c "docker info"
./start-compose.sh
./stop-compose.sh
bash overlay_heartbeat_v2/dev-start-compose.sh
bash overlay_heartbeat_v2/dev-stop-compose.sh
```

No `DOCKER_HOST` unset was required because it was already unset.
No context switch was required because `desktop-linux` was already the active context.

## After State
- context: `desktop-linux`
- `DOCKER_HOST`: unset
- socket: `unix:///Users/marekczarnecki/.docker/run/docker.sock`
- filesystem state after fix:
  - `~/.docker/run/docker.sock` exists
  - `~/.docker/run/user-analytics.otlp.grpc.sock` exists
- `docker info`: succeeds

## Validation
- `docker info`: pass
- subshell `docker info`: pass
- `./start-compose.sh`: pass; preflight succeeded and runtime startup proceeded
- heartbeat wrapper: pass; preflight succeeded and runtime startup proceeded

## Result
pass
