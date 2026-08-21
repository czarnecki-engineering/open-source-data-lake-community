#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/../../.." && pwd -P)"
compose_file="$script_dir/docker-compose.yaml"
# Centralized config: the same file Kubernetes reads to generate its
# shared-credentials Secret (see runtime/knowledge-lake/start-k8s.sh).
# Only this file needs editing to change credentials/config for both stacks.
env_file="$repo_root/runtime/shared/.env"
compose_cmd=(docker compose -f "$compose_file")

if [[ ! -f "$compose_file" ]]; then
  echo "Error: Compose file not found: $compose_file" >&2
  exit 1
fi

if [[ -f "$env_file" ]]; then
  compose_cmd+=(--env-file "$env_file")
else
  echo "WARNING: No .env file found at $env_file. Using defaults from docker-compose.yaml and .env.example" >&2
  echo "To customise configuration: cp runtime/shared/.env.example runtime/shared/.env" >&2
fi

for required_path in \
  "$repo_root/runtime/shared/php" \
  "$repo_root/runtime/shared/config" \
  "$repo_root/runtime/shared/data" \
  "$repo_root/runtime/shared/dags" \
  "$repo_root/runtime/shared/notebooks" \
  "$repo_root/runtime/shared/scripts"; do
  if [[ ! -d "$required_path" ]]; then
    echo "Error: required mount path is missing: $required_path" >&2
    exit 1
  fi
done

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker is not installed." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Error: Docker daemon is not running." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Error: docker compose (v2) is not available." >&2
  exit 1
fi

echo "Starting Compose slice: minio, minio-init, frankenphp, postgres, lakekeeper, trino, airflow-init, airflow-web, airflow-scheduler, jupyter, cloudbeaver"
echo "Building Compose images (${compose_cmd[*]} build)..."
"${compose_cmd[@]}" build

echo "Starting Compose slice (${compose_cmd[*]} up -d): minio, minio-init, frankenphp, postgres, lakekeeper, trino, airflow-init, airflow-web, airflow-scheduler, jupyter, cloudbeaver"
"${compose_cmd[@]}" up -d

echo
cat <<MSG
Compose slice is starting.
- FrankenPHP homepage: http://127.0.0.1:${FRANKENPHP_PORT:-8088}/index.php

Full URL list and validation: bash runtime/foundation/compose/smoke-test.sh
                               runtime/foundation/compose/README.md
Something wrong?               docs/runtime/compose/TROUBLESHOOTING.md
MSG
