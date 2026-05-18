#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image="${CLOAKBROWSER_AGENT_ZERO_IMAGE:-${AGENT_ZERO_IMAGE:-agent0ai/agent-zero:latest}}"
repo="${CLOAKBROWSER_PLUGIN_REPO:-https://github.com/caelx/a0-cloakbrowser-plugin.git}"
scope="${CLOAKBROWSER_INTEGRATION_SCOPE:-full}"
shm_size="${CLOAKBROWSER_DOCKER_SHM_SIZE:-2g}"

mkdir -p "$root/artifacts"

A0_PLUGIN_DOCKER_SHM_SIZE="$shm_size" \
CLOAKBROWSER_INTEGRATION_SCOPE="$scope" \
AGENT_ZERO_IMAGE="$image" python "$root/ci/agent_zero_lifecycle.py" \
  --plugin-name cloakbrowser \
  --repo-url "$repo"
