#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "${script_dir}/.." && pwd -P)"
overlay_compose="overlay_onlyoffice/dev-docker-compose.overlay-onlyoffice.yaml"

if [[ "$(pwd -P)" != "${repo_root}" ]]; then
  echo "Error: run this script from the repository root: cd \"${repo_root}\" && bash ${overlay_compose%/*}/$(basename "$0")" >&2
  exit 1
fi

if [[ ! -f "${repo_root}/stop-compose.sh" ]]; then
  echo "Error: root stop-compose.sh not found at ${repo_root}" >&2
  exit 1
fi

exec bash "${repo_root}/stop-compose.sh" --overlay "${overlay_compose}" "$@"
