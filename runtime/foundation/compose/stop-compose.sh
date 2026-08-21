#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
compose_file="$script_dir/docker-compose.yaml"
compose_cmd=(docker compose -f "$compose_file")

remove_volumes=false
if [[ "${1:-}" == "--volumes" ]]; then
  remove_volumes=true
elif [[ "$#" -gt 0 ]]; then
  echo "Usage: $0 [--volumes]" >&2
  exit 2
fi

if [[ "$remove_volumes" == true ]]; then
  "${compose_cmd[@]}" down --volumes
else
  "${compose_cmd[@]}" down
fi
