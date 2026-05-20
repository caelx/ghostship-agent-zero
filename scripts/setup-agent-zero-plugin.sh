#!/bin/bash
set -euo pipefail

usage() {
  echo "usage: setup-agent-zero-plugin.sh PLUGIN_NAME REPO_ENV [SETUP_ARGS...]" >&2
}

plugin_name="${1:-}"
repo_env="${2:-}"

if [ -z "$plugin_name" ] || [ -z "$repo_env" ]; then
  usage
  exit 2
fi

shift 2
if [ "$#" -eq 0 ]; then
  set -- setup --noninteractive
fi

if [ -f /ins/copy_A0.sh ]; then
  bash /ins/copy_A0.sh local
fi

plugin_dir="$(cd /a0 && PYTHONPATH=/a0 /opt/venv-a0/bin/python /tmp/ghostship/install-agent-zero-plugin.py "$plugin_name" "$repo_env")"
revision="$(awk -F= -v key="$plugin_name" '$1 == key { print $2 }' /tmp/ghostship/plugin-revisions.txt 2>/dev/null || true)"
if [ -n "$revision" ] && [ "$revision" != "latest" ] && [ -d "$plugin_dir/.git" ]; then
  git -C "$plugin_dir" fetch --depth=1 origin "$revision"
  git -C "$plugin_dir" checkout --detach FETCH_HEAD
fi

cd "$plugin_dir"
if [ ! -f execute.py ]; then
  echo "required setup hook missing: $plugin_dir/execute.py" >&2
  exit 1
fi
PYTHONPATH=/a0:"$plugin_dir" /opt/venv-a0/bin/python execute.py "$@"
