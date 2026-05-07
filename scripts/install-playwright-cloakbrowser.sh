#!/bin/bash
set -euo pipefail

. "/ins/setup_venv.sh" local

uv pip install playwright cloakbrowser

export CLOAKBROWSER_CACHE_DIR="${CLOAKBROWSER_CACHE_DIR:-/opt/cloakbrowser}"
export CLOAKBROWSER_AUTO_UPDATE="${CLOAKBROWSER_AUTO_UPDATE:-false}"
mkdir -p "$CLOAKBROWSER_CACHE_DIR"

apt-get update
python -m playwright install-deps chromium

python -m cloakbrowser install
python -m cloakbrowser info
