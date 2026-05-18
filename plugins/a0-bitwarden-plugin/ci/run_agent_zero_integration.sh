#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image="${BITWARDEN_AGENT_ZERO_IMAGE:-${AGENT_ZERO_IMAGE:-agent0ai/agent-zero:latest}}"
repo="${BITWARDEN_PLUGIN_REPO:-https://github.com/caelx/a0-bitwarden-plugin.git}"

mkdir -p "$root/artifacts"

AGENT_ZERO_IMAGE="$image" python "$root/ci/agent_zero_lifecycle.py" \
  --plugin-name bitwarden \
  --repo-url "$repo"
