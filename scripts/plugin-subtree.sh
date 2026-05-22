#!/bin/bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
usage:
  plugin-subtree.sh list
  plugin-subtree.sh pull PLUGIN
  plugin-subtree.sh push PLUGIN

PLUGIN may be one of:
  bitwarden
  cloakbrowser
  provider_opencode_go
  provider_nvidia_build_free
  provider_opencode_zen_free
  provider_openrouter_free
EOF
}

plugin_info() {
  case "${1:-}" in
    bitwarden)
      echo "plugins/a0-bitwarden-plugin git@github.com:caelx/a0-bitwarden-plugin.git"
      ;;
    cloakbrowser)
      echo "plugins/a0-cloakbrowser-plugin git@github.com:caelx/a0-cloakbrowser-plugin.git"
      ;;
    provider_opencode_go)
      echo "plugins/a0-opencode-go-provider-plugin git@github.com:caelx/a0-opencode-go-provider-plugin.git"
      ;;
    provider_nvidia_build_free)
      echo "plugins/a0-nvidia-build-free-provider-plugin git@github.com:caelx/a0-nvidia-build-free-provider-plugin.git"
      ;;
    provider_opencode_zen_free)
      echo "plugins/a0-opencode-zen-free-provider-plugin git@github.com:caelx/a0-opencode-zen-free-provider-plugin.git"
      ;;
    provider_openrouter_free)
      echo "plugins/a0-openrouter-free-provider-plugin git@github.com:caelx/a0-openrouter-free-provider-plugin.git"
      ;;
    *)
      return 1
      ;;
  esac
}

list_plugins() {
  for plugin in \
    bitwarden \
    cloakbrowser \
    provider_opencode_go \
    provider_nvidia_build_free \
    provider_opencode_zen_free \
    provider_openrouter_free
  do
    read -r prefix repo < <(plugin_info "$plugin")
    printf '%s\t%s\t%s\n' "$plugin" "$prefix" "$repo"
  done
}

command="${1:-}"
plugin="${2:-}"

case "$command" in
  list)
    list_plugins
    ;;
  pull)
    if ! read -r prefix repo < <(plugin_info "$plugin"); then
      usage
      exit 2
    fi
    git subtree pull --prefix="$prefix" "$repo" main
    ;;
  push)
    if ! read -r prefix repo < <(plugin_info "$plugin"); then
      usage
      exit 2
    fi
    git subtree push --prefix="$prefix" "$repo" main
    ;;
  *)
    usage
    exit 2
    ;;
esac
