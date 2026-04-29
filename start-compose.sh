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
required_env_vars=(
  AIRFLOW_POSTGRES_USER
  AIRFLOW_POSTGRES_PASSWORD
  AIRFLOW_POSTGRES_DB
  AIRFLOW_ADMIN_USERNAME
  AIRFLOW_ADMIN_PASSWORD
  AIRFLOW_ADMIN_EMAIL
  MINIO_ROOT_USER
  MINIO_ROOT_PASSWORD
  JUPYTER_TOKEN
  PHP_PORT
  AIRFLOW_PORT
  JUPYTER_PORT
  MINIO_API_PORT
  MINIO_CONSOLE_PORT
  AWS_DEFAULT_REGION
  AIRFLOW_UID
  AIRFLOW_VAR_ASX_TICKERS
  AIRFLOW_PIP_ADDITIONAL_REQUIREMENTS
  TZ
  ENABLED_SOLUTION_TAGS
)

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

validate_overlay_file() {
  local overlay_file="${1}"

  if grep -Eq '^[[:space:]]{2}airflow:[[:space:]]*$' "${overlay_file}"; then
    echo "Error: logical service 'airflow' is not supported: ${overlay_file}" >&2
    exit 1
  fi
}

trim_whitespace() {
  local value="${1}"

  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"

  printf '%s' "${value}"
}

read_env_value_from_file() {
  local env_file="${1}"
  local wanted_var="${2}"
  local line=""
  local parsed_var=""
  local parsed_value=""

  while IFS= read -r line || [[ -n "${line}" ]]; do
    if [[ "${line}" =~ ^[[:space:]]*$ ]] || [[ "${line}" =~ ^[[:space:]]*# ]]; then
      continue
    fi

    if [[ "${line}" =~ ^[[:space:]]*(export[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=(.*)$ ]]; then
      parsed_var="${BASH_REMATCH[2]}"
      parsed_value="${BASH_REMATCH[3]}"
      if [[ "${parsed_var}" == "${wanted_var}" ]]; then
        printf '%s\n' "${parsed_value}"
        return 0
      fi
    fi
  done < "${env_file}"

  return 1
}

env_value_is_blank() {
  local raw_value="${1}"
  local trimmed_value=""
  local first_char=""
  local last_char=""

  trimmed_value="$(trim_whitespace "${raw_value}")"

  if [[ "${#trimmed_value}" -ge 2 ]]; then
    first_char="${trimmed_value:0:1}"
    last_char="${trimmed_value: -1}"
    if [[ ( "${first_char}" == '"' && "${last_char}" == '"' ) || ( "${first_char}" == "'" && "${last_char}" == "'" ) ]]; then
      trimmed_value="${trimmed_value:1:${#trimmed_value}-2}"
    fi
  fi

  trimmed_value="$(trim_whitespace "${trimmed_value}")"
  [[ -z "${trimmed_value}" ]]
}

validate_required_env_file() {
  local env_file="${1}"
  local env_example_path="${script_dir}/.env.example"
  local var_name=""
  local raw_value=""
  local missing_vars=()
  local blank_vars=()

  if [[ ! -f "${env_file}" ]]; then
    echo "Error: required env file not found: ${env_file}" >&2
    echo "Copy or update ${env_file} from ${env_example_path} before starting the Community runtime." >&2
    exit 1
  fi

  for var_name in "${required_env_vars[@]}"; do
    if ! raw_value="$(read_env_value_from_file "${env_file}" "${var_name}")"; then
      missing_vars+=("${var_name}")
      continue
    fi

    if env_value_is_blank "${raw_value}"; then
      blank_vars+=("${var_name}")
    fi
  done

  if (( ${#missing_vars[@]} > 0 || ${#blank_vars[@]} > 0 )); then
    echo "Error: required Community env values are incomplete in ${env_file}" >&2
    if (( ${#missing_vars[@]} > 0 )); then
      echo "Missing required variables:" >&2
      printf '  - %s\n' "${missing_vars[@]}" >&2
    fi
    if (( ${#blank_vars[@]} > 0 )); then
      echo "Blank required variables:" >&2
      printf '  - %s\n' "${blank_vars[@]}" >&2
    fi
    echo "Copy or update ${env_file} from ${env_example_path} before starting the Community runtime." >&2
    exit 1
  fi
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

    validate_overlay_file "${overlay_file}"
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

validate_required_env_file "${script_dir}/.env"

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
