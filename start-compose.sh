#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF' >&2
Usage:
  ./start-compose.sh [--overlay <compose-file>]

Options:
  --overlay <compose-file>   Optional overlay compose file.
EOF
}

compose_cmd=(docker compose -f docker-compose.yaml)
overlay_file=""

if [[ "${#}" -gt 0 ]]; then
  if [[ "${#}" -ne 2 || "${1}" != "--overlay" ]]; then
    usage
    exit 2
  fi
  overlay_file="${2}"
fi

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
else
  script_dir="$(pwd -P)"
fi

if [[ "$(pwd -P)" != "${script_dir}" ]]; then
  echo "Error: run this script from the repo root: cd \"${script_dir}\" && ./start-compose.sh" >&2
  exit 1
fi

if [[ ! -f "docker-compose.yaml" ]]; then
  echo "Error: docker-compose.yaml not found in current directory. Run from the repo root." >&2
  exit 1
fi

if [[ -n "${overlay_file}" ]]; then
  if [[ ! -f "${overlay_file}" ]]; then
    echo "Error: overlay compose file not found: ${overlay_file}" >&2
    exit 1
  fi
  compose_cmd+=(-f "${overlay_file}")
fi

if [ ! -f ".env" ]; then
  echo "WARNING: No .env file found. Using defaults from docker-compose.yaml"
  echo "To customise configuration, run: cp .env.example .env"
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker is not installed. Install Docker Desktop (or Docker Engine) and try again." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Error: Docker daemon is not running. Start Docker Desktop and try again." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Error: docker compose (v2) is not available. Update Docker Desktop / install the Docker Compose plugin and try again." >&2
  exit 1
fi

echo "Building images (${compose_cmd[*]} build)..."
"${compose_cmd[@]}" build

echo "Starting stack (${compose_cmd[*]} up -d)..."
"${compose_cmd[@]}" up -d

echo "Waiting briefly for services to initialize..."
sleep 5

cat <<'EOF'

Stack is starting. Default access URLs (may differ if overridden via .env):
- Airflow:        http://localhost:8080
- MinIO Console:  http://localhost:9001
- MinIO API:      http://localhost:9000
- Jupyter:        http://localhost:8888
- PHP:            http://localhost:8088
EOF
