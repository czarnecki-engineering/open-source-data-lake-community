#!/usr/bin/env bash
set -euo pipefail

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
else
  script_dir="$(pwd -P)"
fi

repo_root="$(cd -- "${script_dir}/.." && pwd -P)"

exec "${repo_root}/stop-compose.sh" --overlay "overlay_heartbeat_v2/dev-docker-compose.overlay-heartbeat-v2.yaml" "$@"
