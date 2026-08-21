#!/usr/bin/env bash
# Compose equivalent of runtime/knowledge-lake/validate-config-first.sh.
# The host-side checks (canonical file, no duplicates, no symlinks) are
# identical to the k8s version — they check runtime/shared/, which both
# stacks read from — the only difference is how in-container visibility
# is checked (docker exec vs kubectl exec).

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../../.." && pwd)"
ODL_MOUNT_DIR="${REPO_ROOT}/runtime/shared"
CANONICAL_CONFIG_PATH="${ODL_MOUNT_DIR}/config/dags/heartbeat.json"
AIRFLOW_CONTAINER="airflow-scheduler"
JUPYTER_CONTAINER="jupyter"
FRANKENPHP_CONTAINER="frankenphp"

FAILURES=0

pass() {
  echo "PASS: $*"
}

fail() {
  echo "FAIL: $*" >&2
  FAILURES=$((FAILURES + 1))
}

skip() {
  echo "SKIP: $*"
}

require_bin() {
  local name="$1"
  if command -v "${name}" >/dev/null 2>&1; then
    pass "found required command '${name}'"
  else
    fail "missing required command '${name}'"
  fi
}

check_file_exists() {
  local path="$1"
  if [[ -f "${path}" ]]; then
    pass "canonical config file exists at ${path}"
  else
    fail "canonical config file is missing at ${path}"
  fi
}

check_json_parse() {
  local path="$1"
  if python3 - "${path}" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
if not isinstance(payload, dict):
    raise SystemExit("Heartbeat config must be a JSON object.")
required = {"interval", "message_format"}
missing = sorted(required - payload.keys())
if missing:
    raise SystemExit(f"Heartbeat config is missing keys: {missing}")
PY
  then
    pass "canonical heartbeat config parsed as JSON object with required keys"
  else
    fail "canonical heartbeat config did not parse as the expected JSON object"
  fi
}

check_absent_duplicate_dirs() {
  local candidate
  for candidate in \
    "${ODL_MOUNT_DIR}/dags/config" \
    "${ODL_MOUNT_DIR}/notebooks/config" \
    "${ODL_MOUNT_DIR}/php/config"; do
    if [[ -e "${candidate}" ]]; then
      fail "unexpected config directory exists outside canonical config root: ${candidate}"
    else
      pass "no duplicate config directory at ${candidate}"
    fi
  done
}

check_duplicate_heartbeat_configs() {
  local matches=()
  local line
  while IFS= read -r line; do
    matches+=("${line}")
  done < <(find "${REPO_ROOT}" -name 'heartbeat.json' -print | sort)

  if [[ "${#matches[@]}" -ne 1 ]]; then
    fail "expected exactly one heartbeat.json in the repository, found ${#matches[@]}"
    printf 'Observed heartbeat.json paths:\n' >&2
    printf '%s\n' "${matches[@]}" >&2
    return
  fi

  if [[ "${matches[0]}" == "${CANONICAL_CONFIG_PATH}" ]]; then
    pass "exactly one heartbeat.json exists and it is the canonical config file"
  else
    fail "heartbeat.json exists only at unexpected path: ${matches[0]}"
  fi
}

check_config_symlinks() {
  local matches=()
  local line
  while IFS= read -r line; do
    matches+=("${line}")
  done < <(find "${ODL_MOUNT_DIR}" -type l -print | sort)

  if [[ "${#matches[@]}" -eq 0 ]]; then
    pass "no symlink-based config workarounds exist under ${ODL_MOUNT_DIR}"
  else
    fail "unexpected symlinks exist under ${ODL_MOUNT_DIR}"
    printf 'Observed symlinks:\n' >&2
    printf '%s\n' "${matches[@]}" >&2
  fi
}

stack_running() {
  docker inspect --format '{{.State.Status}}' "${FRANKENPHP_CONTAINER}" 2>/dev/null | grep -qx running
}

check_container_running() {
  local container="$1"
  if docker inspect --format '{{.State.Status}}' "${container}" 2>/dev/null | grep -qx running; then
    pass "container/${container} is running"
  else
    fail "container/${container} is not running"
  fi
}

host_sha256() {
  shasum -a 256 "${CANONICAL_CONFIG_PATH}" | awk '{print $1}'
}

airflow_sha256() {
  docker exec "${AIRFLOW_CONTAINER}" sh -lc \
    "python -c \"import hashlib, pathlib; print(hashlib.sha256(pathlib.Path('/opt/airflow/config/dags/heartbeat.json').read_bytes()).hexdigest())\""
}

jupyter_sha256() {
  docker exec "${JUPYTER_CONTAINER}" sh -lc \
    "python -c \"import hashlib, pathlib; print(hashlib.sha256(pathlib.Path('/home/jovyan/config/dags/heartbeat.json').read_bytes()).hexdigest())\""
}

frankenphp_sha256() {
  docker exec "${FRANKENPHP_CONTAINER}" sh -lc \
    "php -r \"echo hash_file('sha256', '/app/config/dags/heartbeat.json'), PHP_EOL;\""
}

compare_hash() {
  local name="$1"
  local observed="$2"
  local expected="$3"

  if [[ "${observed}" == "${expected}" ]]; then
    pass "${name} sees the canonical heartbeat config content"
  else
    fail "${name} hash did not match canonical host config"
  fi
}

check_runtime_visibility() {
  local expected_hash
  expected_hash="$(host_sha256)"
  pass "computed canonical host config SHA256 ${expected_hash}"

  compare_hash "Airflow scheduler" "$(airflow_sha256)" "${expected_hash}"
  compare_hash "Jupyter" "$(jupyter_sha256)" "${expected_hash}"
  compare_hash "FrankenPHP" "$(frankenphp_sha256)" "${expected_hash}"
}

echo "==> Validating config-first runtime pattern (Compose)"

require_bin docker
require_bin python3
require_bin shasum

check_file_exists "${CANONICAL_CONFIG_PATH}"
check_json_parse "${CANONICAL_CONFIG_PATH}"
check_absent_duplicate_dirs
check_duplicate_heartbeat_configs
check_config_symlinks

if stack_running; then
  check_container_running "${AIRFLOW_CONTAINER}"
  check_container_running "${JUPYTER_CONTAINER}"
  check_container_running "${FRANKENPHP_CONTAINER}"
  if (( FAILURES == 0 )); then
    check_runtime_visibility
  fi
else
  skip "Compose stack is not running; skipped in-container config visibility checks"
fi

if (( FAILURES > 0 )); then
  echo "Config-first validation failed with ${FAILURES} failing check(s)." >&2
  exit 1
fi

echo "Config-first validation passed."
