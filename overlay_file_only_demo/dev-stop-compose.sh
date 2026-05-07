#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

./stop-compose.sh --overlay overlay_file_only_demo/dev-docker-compose.overlay-file-only-demo.yaml
