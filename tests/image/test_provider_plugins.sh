#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/lib.sh"

echo "checking standalone provider plugin installs"
run_bash_in_image '. /ins/setup_venv.sh local && cd /a0 && PYTHONPATH=/a0 python - <<'"'"'PY'"'"'
from pathlib import Path

from helpers import plugins
from helpers.providers import ProviderManager

expected = {
    "provider_ollama_cloud": "ollama_cloud",
    "provider_opencode_go": "opencode_go",
    "provider_nvidia_build_free": "nvidia_build_free",
    "provider_opencode_zen_free": "opencode_zen_free",
    "provider_openrouter_free": "openrouter_free",
}

for plugin_name, provider_id in expected.items():
    plugin_dir = plugins.find_plugin_dir(plugin_name)
    if not plugin_dir:
        raise AssertionError(f"plugin not installed: {plugin_name}")
    root = Path(plugin_dir)
    for required in ("plugin.yaml", "conf/model_providers.yaml", "webui/config.html"):
        path = root / required
        if not path.is_file():
            raise AssertionError(f"installed plugin missing {required}: {path}")
    provider_yaml = (root / "conf/model_providers.yaml").read_text(encoding="utf-8")
    if f"{provider_id}:" not in provider_yaml:
        raise AssertionError(f"provider id missing from plugin config: {provider_id}")

chat_ids = {provider["id"] for provider in ProviderManager.get_instance().get_raw_providers("chat")}
missing = sorted(set(expected.values()) - chat_ids)
if missing:
    raise AssertionError(f"provider manager did not load provider ids: {missing}; ids={sorted(chat_ids)}")

print(f"standalone provider plugins are installed and registered: {sorted(expected.values())}", flush=True)
PY'
