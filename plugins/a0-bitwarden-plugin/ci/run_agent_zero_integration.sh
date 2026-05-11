#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image="${BITWARDEN_AGENT_ZERO_IMAGE:-${AGENT_ZERO_IMAGE:-agent0ai/agent-zero:latest}}"
repo="${BITWARDEN_PLUGIN_REPO:-file:///plugin-src}"

mkdir -p "$root/artifacts"

docker run --rm --shm-size=2g \
  -e BITWARDEN_PLUGIN_REPO="$repo" \
  -e BITWARDEN_LIVE_TEST="${BITWARDEN_LIVE_TEST:-0}" \
  -e BW_CLIENT_ID="${BW_CLIENT_ID:-}" \
  -e BW_CLIENT_SECRET="${BW_CLIENT_SECRET:-}" \
  -e BW_PASSWORD="${BW_PASSWORD:-}" \
  -v "$root:/plugin-src:ro" \
  -v "$root/artifacts:/artifacts" \
  "$image" \
  bash -lc '
    set -euo pipefail
    . /ins/setup_venv.sh local
    mkdir -p /artifacts
    cd /a0
    python - <<PY
import sys
sys.path.insert(0, "/git/agent-zero")
from plugins._plugin_installer.helpers.install import install_from_git
from helpers import plugins
repo = "'"$repo"'"
if not plugins.find_plugin_dir("bitwarden"):
    print(install_from_git(repo, plugin_name="bitwarden"))
PY
    plugin_dir="$(python - <<PY
import sys
sys.path.insert(0, "/git/agent-zero")
from helpers import plugins
print(plugins.find_plugin_dir("bitwarden") or "")
PY
)"
    test -n "$plugin_dir"
    cd "$plugin_dir"
    ln -sfn /artifacts artifacts
    python execute.py --json > /artifacts/plugin-status.json
    python ci/collect_versions.py
    python ci/run_setup_smoke.py
    python ci/run_mcp_config_smoke.py
    python ci/run_skill_smoke.py
    if [ "${BITWARDEN_LIVE_TEST:-0}" = "1" ]; then
      bw status > /artifacts/bw-live-status.json
    fi
    python ci/run_uninstall_restore.py
  '
