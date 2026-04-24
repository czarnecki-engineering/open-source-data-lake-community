#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF' >&2
Usage:
  ./stop-compose.sh [--overlay <compose-file-or-name>]... [--volumes]

Options:
  --overlay <compose-file-or-name>   Optional overlay compose file path or overlay name.
                                      May be repeated. If the value is not an
                                      existing file, the wrapper resolves it via:
                                      1. overlay_<name>/dev-docker-compose.overlay-<slug>.yaml
                                      2. overlay_<name>/docker-compose.overlay-<slug>.yaml
                                      3. overlay_<name>/overlay_<name>/docker-compose.overlay-<slug>.yaml
  --volumes   Remove volumes (docker compose down -v)
EOF
}

remove_volumes=false
overlay_args=()
overlay_files=()

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
      overlay_args+=("${2}")
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
