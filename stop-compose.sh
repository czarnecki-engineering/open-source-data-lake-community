#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF' >&2
Usage:
  ./stop-compose.sh [--overlay <compose-file>] [--volumes]

Options:
  --overlay <compose-file>   Optional overlay compose file.
  --volumes   Remove volumes (docker compose down -v)
EOF
}

remove_volumes=false
overlay_file=""

while [[ "${#}" -gt 0 ]]; do
  case "${1}" in
    --volumes)
      remove_volumes=true
      shift
      ;;
    --overlay)
      if [[ "${#}" -lt 2 ]]; then
        usage
        exit 2
      fi
      overlay_file="${2}"
      shift 2
      ;;
    *)
      usage
      exit 2
      ;;
  esac
done

compose_cmd=(docker compose -f docker-compose.yaml)

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

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker is not installed." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Error: docker compose (v2) is not available." >&2
  exit 1
fi

if [[ "${remove_volumes}" == "true" ]]; then
  echo "Stopping stack and removing volumes (${compose_cmd[*]} down -v)..."
  "${compose_cmd[@]}" down -v
else
  echo "Stopping stack (${compose_cmd[*]} down)... (volumes preserved)"
  "${compose_cmd[@]}" down
fi
