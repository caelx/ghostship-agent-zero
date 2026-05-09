#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/lib.sh"

image="${1:-}"

if [ -z "$image" ]; then
  echo "usage: $0 IMAGE" >&2
  exit 2
fi

echo "checking provider plugins"
run_bash_in_image '
for plugin in provider_ollama_cloud provider_opencode_go provider_nvidia_build_free provider_opencode_zen_free provider_openrouter_free; do
  test -f "/a0/usr/plugins/$plugin/plugin.yaml"
  test -f "/a0/usr/plugins/$plugin/conf/model_providers.yaml"
  test -f "/a0/usr/plugins/$plugin/webui/config.html"
done

grep -q "ollama_cloud:" /a0/usr/plugins/provider_ollama_cloud/conf/model_providers.yaml
grep -q "litellm_provider: ollama" /a0/usr/plugins/provider_ollama_cloud/conf/model_providers.yaml
grep -q "opencode_go:" /a0/usr/plugins/provider_opencode_go/conf/model_providers.yaml
grep -q "litellm_provider: openai" /a0/usr/plugins/provider_opencode_go/conf/model_providers.yaml

grep -q "nvidia_build_free:" /a0/usr/plugins/provider_nvidia_build_free/conf/model_providers.yaml
grep -q "opencode_zen_free:" /a0/usr/plugins/provider_opencode_zen_free/conf/model_providers.yaml
grep -q "openrouter_free:" /a0/usr/plugins/provider_openrouter_free/conf/model_providers.yaml
grep -q "/api/plugins/provider_nvidia_build_free/models" /a0/usr/plugins/provider_nvidia_build_free/conf/model_providers.yaml
grep -q "/api/plugins/provider_opencode_zen_free/models" /a0/usr/plugins/provider_opencode_zen_free/conf/model_providers.yaml
grep -q "/api/plugins/provider_openrouter_free/models" /a0/usr/plugins/provider_openrouter_free/conf/model_providers.yaml

for plugin in provider_nvidia_build_free provider_opencode_zen_free provider_openrouter_free; do
  test -f "/a0/usr/plugins/$plugin/api/models.py"
  grep -q "class Models(ApiHandler)" "/a0/usr/plugins/$plugin/api/models.py"
done

! grep -R "provider_openrouter_free\|provider_opencode_zen_free\|provider_nvidia_build_free" /git/agent-zero/plugins/_model_config /git/agent-zero/helpers/providers.py
'
