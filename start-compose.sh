#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF' >&2
Usage:
  ./start-compose.sh [--overlay <compose-file-or-name>]...

Options:
  --overlay <compose-file-or-name>   Optional overlay compose file path or overlay name.
                                      May be repeated. If the value is not an
                                      existing file, the wrapper resolves it via:
                                      1. overlay_<name>/dev-docker-compose.overlay-<slug>.yaml
                                      2. overlay_<name>/docker-compose.overlay-<slug>.yaml
                                      3. overlay_<name>/overlay_<name>/docker-compose.overlay-<slug>.yaml
EOF
}

compose_cmd=(docker compose -f docker-compose.yaml)
overlay_args=()
overlay_files=()

while [[ "${#}" -gt 0 ]]; do
  case "${1}" in
    --overlay)
      if [[ "${#}" -lt 2 ]]; then
        usage
        exit 2
      fi
      overlay_args+=("${2}")
      shift 2
      ;;
    *)
      usage
      exit 2
      ;;
  esac
done

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

resolve_overlay_file() {
  local overlay_arg="${1}"
  local overlay_slug
  local -a candidates=()

  if [[ -f "${overlay_arg}" ]]; then
    printf '%s\n' "${overlay_arg}"
    return 0
  fi

  overlay_slug="${overlay_arg//_/-}"
  candidates+=("overlay_${overlay_arg}/dev-docker-compose.overlay-${overlay_slug}.yaml")
  candidates+=("overlay_${overlay_arg}/docker-compose.overlay-${overlay_slug}.yaml")
  candidates+=("overlay_${overlay_arg}/overlay_${overlay_arg}/docker-compose.overlay-${overlay_slug}.yaml")

  for candidate in "${candidates[@]}"; do
    if [[ -f "${candidate}" ]]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done

  return 1
}

overlay_already_selected() {
  local candidate="${1}"
  local existing

  for existing in "${overlay_files[@]:-}"; do
    if [[ "${existing}" == "${candidate}" ]]; then
      return 0
    fi
  done

  return 1
}

if (( ${#overlay_args[@]:-0} > 0 )); then
  for overlay_arg in "${overlay_args[@]}"; do
    if ! overlay_file="$(resolve_overlay_file "${overlay_arg}")"; then
      echo "Error: overlay compose file not found: ${overlay_arg}" >&2
      exit 1
    fi

    if overlay_already_selected "${overlay_file}"; then
      echo "Error: duplicate overlay compose file requested: ${overlay_file}" >&2
      exit 1
    fi

    overlay_files+=("${overlay_file}")
    compose_cmd+=(-f "${overlay_file}")
  done
fi

if (( ${#overlay_files[@]:-0} > 0 )); then
  printf 'Resolved overlays (merge order):\n' >&2
  for overlay_file in "${overlay_files[@]}"; do
    printf -- '- %s\n' "${overlay_file}" >&2
  done
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
