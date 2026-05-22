#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/lib.sh"

echo "checking CloakBrowser plugin is not installed by default"
run_bash_in_image '. /ins/setup_venv.sh local && cd /a0 && PYTHONPATH=/a0 python - <<'"'"'PY'"'"'
from helpers import plugins

plugin_dir = plugins.find_plugin_dir("cloakbrowser")
if plugin_dir and str(plugin_dir).startswith("/a0/usr/plugins/"):
    raise AssertionError(f"CloakBrowser plugin should not be custom-installed by default: {plugin_dir}")

print("CloakBrowser plugin is absent by default", flush=True)
PY'
