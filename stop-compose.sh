#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF' >&2
Usage:
  ./stop-compose.sh [--volumes]

Options:
  --volumes   Remove volumes (docker compose down -v)
EOF
}

remove_volumes=false
if [[ "${#}" -gt 1 ]]; then
  usage
  exit 2
fi
if [[ "${#}" -eq 1 ]]; then
  if [[ "${1}" == "--volumes" ]]; then
    remove_volumes=true
  else
    usage
    exit 2
  fi
fi

if [[ ! -f "docker-compose.yaml" ]]; then
  echo "Error: docker-compose.yaml not found in current directory. Run from the repo root." >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker is not installed." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Error: docker compose (v2) is not available." >&2
  exit 1
fi

if [[ "${remove_volumes}" == "true" ]]; then
  echo "Stopping stack and removing volumes (docker compose down -v)..."
  docker compose down -v
else
  echo "Stopping stack (docker compose down)... (volumes preserved)"
  docker compose down
fi

