#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image="${AGENT_ZERO_IMAGE:-agent0ai/agent-zero:latest}"
repo="${PROVIDER_PLUGIN_REPO:-https://github.com/caelx/a0-opencode-zen-free-provider-plugin.git}"

mkdir -p "$root/artifacts"

AGENT_ZERO_IMAGE="$image" python "$root/ci/agent_zero_lifecycle.py" \
  --plugin-name provider_opencode_zen_free \
  --provider-id opencode_zen_free \
  --repo-url "$repo"
