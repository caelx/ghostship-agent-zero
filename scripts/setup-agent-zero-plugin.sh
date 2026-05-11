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

plugin_dir="$(cd /a0 && /opt/venv-a0/bin/python /tmp/ghostship/install-agent-zero-plugin.py "$plugin_name" "$repo_env")"
mkdir -p /a0/usr/plugins
target="/a0/usr/plugins/$plugin_name"
if [ "$plugin_dir" != "$target" ]; then
  rm -rf "$target"
  cp -a "$plugin_dir" "$target"
fi

cd "$target"
if [ -f execute.py ]; then
  /opt/venv-a0/bin/python execute.py "$@"
fi
