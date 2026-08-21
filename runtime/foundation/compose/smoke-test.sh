#!/usr/bin/env bash
# Compose equivalent of runtime/knowledge-lake/smoke-test.sh. Mirrors its
# checks and messaging conventions so both stacks are validated the same
# way: required tools, public entry containers healthy, public URLs
# respond, and the live repo-backed mounts actually work bidirectionally.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../../.." && pwd)"
MOUNT_DIR="${REPO_ROOT}/runtime/shared"
PHP_DIR="${MOUNT_DIR}/php"
NOTEBOOKS_DIR="${MOUNT_DIR}/notebooks"
DATA_DIR="${MOUNT_DIR}/data"
ENV_FILE="${MOUNT_DIR}/.env"
FRANKENPHP_CONTAINER="frankenphp"
JUPYTER_CONTAINER="jupyter"

# Same centralized config file the stack itself reads (see start-compose.sh).
# .env is KEY=value data, not a shell script (values like
# AIRFLOW_PIP_ADDITIONAL_REQUIREMENTS contain unquoted spaces that break a
# plain `source`) — extract only the two port values needed here, the same
# way docker-compose/--from-env-file read it, rather than sourcing the file.
env_var() {
  local key="$1"
  [[ -f "${ENV_FILE}" ]] || return 0
  grep -E "^${key}=" "${ENV_FILE}" | tail -1 | cut -d= -f2-
}

FRANKENPHP_PORT="$(env_var FRANKENPHP_PORT)"
JUPYTER_PORT="$(env_var JUPYTER_PORT)"

PHP_URL="http://127.0.0.1:${FRANKENPHP_PORT:-8088}/index.php"
JUPYTER_URL="http://127.0.0.1:${JUPYTER_PORT:-8888}"

PHP_MARKER="compose-php-smoke-$$"
PHP_TEST_FILE="${PHP_DIR}/.smoke-test.php"
NOTEBOOK_POD_FILE=".smoke-from-container-$$.txt"
NOTEBOOK_HOST_FILE=".smoke-from-host-$$.txt"
NOTEBOOK_POD_PATH="/home/jovyan/work/${NOTEBOOK_POD_FILE}"
NOTEBOOK_HOST_PATH="${NOTEBOOKS_DIR}/${NOTEBOOK_HOST_FILE}"
DATA_POD_FILE=".data-smoke-from-container-$$.txt"
DATA_HOST_FILE=".data-smoke-from-host-$$.txt"
DATA_POD_PATH="/home/jovyan/data/${DATA_POD_FILE}"
DATA_HOST_PATH="${DATA_DIR}/${DATA_HOST_FILE}"

FAILURES=0

cleanup() {
  rm -f "${PHP_TEST_FILE}" "${NOTEBOOKS_DIR}/${NOTEBOOK_POD_FILE}" "${NOTEBOOK_HOST_PATH}" "${DATA_DIR}/${DATA_POD_FILE}" "${DATA_HOST_PATH}"
  docker exec "${JUPYTER_CONTAINER}" sh -lc \
    "rm -f '${NOTEBOOK_POD_PATH}' '/home/jovyan/work/${NOTEBOOK_HOST_FILE}' '${DATA_POD_PATH}' '/home/jovyan/data/${DATA_HOST_FILE}'" >/dev/null 2>&1 || true
}

trap cleanup EXIT

pass() {
  echo "PASS: $*"
}

fail() {
  echo "FAIL: $*" >&2
  FAILURES=$((FAILURES + 1))
}

require_bin() {
  local name="$1"
  if command -v "${name}" >/dev/null 2>&1; then
    pass "found required command '${name}'"
  else
    fail "missing required command '${name}'"
  fi
}

check_container_healthy() {
  local container="$1"
  local state
  state="$(docker inspect --format '{{.State.Status}}' "${container}" 2>/dev/null || true)"

  if [[ -z "${state}" ]]; then
    fail "container '${container}' is not running (not found)"
    return
  fi
  if [[ "${state}" != "running" ]]; then
    fail "container '${container}' is not running (state: ${state})"
    return
  fi

  local health
  health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "${container}" 2>/dev/null || true)"
  if [[ "${health}" == "none" || "${health}" == "healthy" ]]; then
    pass "container '${container}' is running (health: ${health})"
  else
    fail "container '${container}' is running but not healthy (health: ${health})"
  fi
}

check_url() {
  local name="$1"
  local url="$2"
  if curl --silent --show-error --fail "${url}" >/dev/null; then
    pass "${name} responded at ${url}"
  else
    fail "${name} did not respond at ${url}"
  fi
}

check_php_live_mount() {
  printf '<?php echo "%s";\n' "${PHP_MARKER}" > "${PHP_TEST_FILE}"

  local response
  if ! response="$(curl --silent --show-error --fail "http://127.0.0.1:${FRANKENPHP_PORT:-8088}/.smoke-test.php")"; then
    fail "FrankenPHP did not serve temporary repo-mounted test file"
    return
  fi

  if [[ "${response}" == "${PHP_MARKER}" ]]; then
    pass "FrankenPHP live repo mount served host-written PHP content"
  else
    fail "FrankenPHP live repo mount returned unexpected content: ${response}"
  fi
}

check_jupyter_live_mount() {
  local pod_marker="compose-jupyter-container-smoke-$$"
  local host_marker="compose-jupyter-host-smoke-$$"
  local pod_readback
  local host_readback

  if docker exec "${JUPYTER_CONTAINER}" sh -lc \
    "printf '%s\n' '${pod_marker}' > '${NOTEBOOK_POD_PATH}'"; then
    pass "Jupyter container wrote to ${NOTEBOOK_POD_PATH}"
  else
    fail "Jupyter container could not write to ${NOTEBOOK_POD_PATH}"
    return
  fi

  if [[ -f "${NOTEBOOKS_DIR}/${NOTEBOOK_POD_FILE}" ]]; then
    host_readback="$(cat "${NOTEBOOKS_DIR}/${NOTEBOOK_POD_FILE}")"
    if [[ "${host_readback}" == "${pod_marker}" ]]; then
      pass "host observed Jupyter container-written file in ${NOTEBOOKS_DIR}"
    else
      fail "host observed unexpected content for container-written Jupyter file: ${host_readback}"
    fi
  else
    fail "host did not observe Jupyter container-written file in ${NOTEBOOKS_DIR}"
  fi

  printf '%s\n' "${host_marker}" > "${NOTEBOOK_HOST_PATH}"
  if pod_readback="$(docker exec "${JUPYTER_CONTAINER}" sh -lc "cat '/home/jovyan/work/${NOTEBOOK_HOST_FILE}'" 2>/dev/null)"; then
    if [[ "${pod_readback}" == "${host_marker}" ]]; then
      pass "Jupyter container observed host-written file in /home/jovyan/work"
    else
      fail "Jupyter container observed unexpected content for host-written file: ${pod_readback}"
    fi
  else
    fail "Jupyter container could not read host-written file from /home/jovyan/work"
  fi
}

check_jupyter_data_mount() {
  local pod_marker="compose-jupyter-data-container-smoke-$$"
  local host_marker="compose-jupyter-data-host-smoke-$$"
  local pod_readback
  local host_readback

  if docker exec "${JUPYTER_CONTAINER}" sh -lc \
    "printf '%s\n' '${pod_marker}' > '${DATA_POD_PATH}'"; then
    pass "Jupyter container wrote to ${DATA_POD_PATH}"
  else
    fail "Jupyter container could not write to ${DATA_POD_PATH}"
    return
  fi

  if [[ -f "${DATA_DIR}/${DATA_POD_FILE}" ]]; then
    host_readback="$(cat "${DATA_DIR}/${DATA_POD_FILE}")"
    if [[ "${host_readback}" == "${pod_marker}" ]]; then
      pass "host observed Jupyter container-written file in ${DATA_DIR}"
    else
      fail "host observed unexpected content for container-written Jupyter data file: ${host_readback}"
    fi
  else
    fail "host did not observe Jupyter container-written file in ${DATA_DIR}"
  fi

  printf '%s\n' "${host_marker}" > "${DATA_HOST_PATH}"
  if pod_readback="$(docker exec "${JUPYTER_CONTAINER}" sh -lc "cat '/home/jovyan/data/${DATA_HOST_FILE}'" 2>/dev/null)"; then
    if [[ "${pod_readback}" == "${host_marker}" ]]; then
      pass "Jupyter container observed host-written file in /home/jovyan/data"
    else
      fail "Jupyter container observed unexpected content for host-written data file: ${pod_readback}"
    fi
  else
    fail "Jupyter container could not read host-written file from /home/jovyan/data"
  fi
}

echo "==> Compose smoke test"

require_bin docker
require_bin curl

if (( FAILURES == 0 )); then
  check_container_healthy "${FRANKENPHP_CONTAINER}"
  check_container_healthy "${JUPYTER_CONTAINER}"
  check_url "FrankenPHP homepage" "${PHP_URL}"
  check_url "Jupyter" "${JUPYTER_URL}"
  check_php_live_mount
  check_jupyter_live_mount
  check_jupyter_data_mount
fi

if (( FAILURES > 0 )); then
  echo "Smoke test failed with ${FAILURES} failing check(s)." >&2
  exit 1
fi

echo "Smoke test passed."
