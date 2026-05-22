#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/lib.sh"

echo "checking provider plugins are not installed by default"
run_bash_in_image '. /ins/setup_venv.sh local && cd /a0 && PYTHONPATH=/a0 python - <<'"'"'PY'"'"'
from helpers import plugins

for plugin_name in (
    "provider_ollama_cloud",
    "provider_opencode_go",
    "provider_nvidia_build_free",
    "provider_opencode_zen_free",
    "provider_openrouter_free",
):
    plugin_dir = plugins.find_plugin_dir(plugin_name)
    if plugin_dir and str(plugin_dir).startswith("/a0/usr/plugins/"):
        raise AssertionError(f"provider plugin should not be custom-installed by default: {plugin_name} -> {plugin_dir}")

print("provider plugins are absent by default", flush=True)
PY'
