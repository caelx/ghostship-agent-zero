#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/lib.sh"

echo "checking Bitwarden plugin is not installed by default"
run_bash_in_image '
plugin_dir="/a0/usr/plugins/bitwarden"
if [ -e "$plugin_dir" ]; then
  echo "Bitwarden plugin should not be custom-installed by default: ${plugin_dir}" >&2
  exit 1
fi
echo "Bitwarden plugin is absent by default"
'
