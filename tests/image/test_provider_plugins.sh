#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/lib.sh"

echo "checking provider plugins are not installed by default"
run_bash_in_image '
for plugin_name in \
  provider_ollama_cloud \
  provider_opencode_go \
  provider_nvidia_build_free \
  provider_opencode_zen_free \
  provider_openrouter_free
do
  plugin_dir="/a0/usr/plugins/${plugin_name}"
  if [ -e "$plugin_dir" ]; then
    echo "provider plugin should not be custom-installed by default: ${plugin_dir}" >&2
    exit 1
  fi
done
echo "provider plugins are absent by default"
'
