#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image="${AGENT_ZERO_IMAGE:-agent0ai/agent-zero:latest}"
plugin_name="provider_opencode_go"
provider_id="opencode_go"
repo="${PROVIDER_PLUGIN_REPO:-https://github.com/caelx/a0-opencode-go-provider-plugin.git}"

mkdir -p "$root/artifacts"

AGENT_ZERO_IMAGE="$image" python "$root/ci/agent_zero_lifecycle.py" \
  --plugin-name "$plugin_name" \
  --provider-id "$provider_id" \
  --repo-url "$repo"
