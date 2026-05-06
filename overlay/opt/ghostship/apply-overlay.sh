#!/bin/bash
set -euo pipefail

export CLOAKBROWSER_CACHE_DIR="${CLOAKBROWSER_CACHE_DIR:-/opt/cloakbrowser}"
export CLOAKBROWSER_AUTO_UPDATE="${CLOAKBROWSER_AUTO_UPDATE:-false}"

if [ ! -f /a0/plugins/_browser/helpers/runtime.py ]; then
  echo "Agent Zero browser runtime not found; skipping Ghostship browser patch"
  exit 0
fi

/opt/ghostship/patch-browser-runtime.py /a0/plugins/_browser/helpers/runtime.py
