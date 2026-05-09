#!/bin/bash
set -euo pipefail

. "/ins/setup_venv.sh" local

uv pip install --upgrade playwright 'cloakbrowser[geoip]'

export CLOAKBROWSER_CACHE_DIR="${CLOAKBROWSER_CACHE_DIR:-/opt/cloakbrowser}"
export CLOAKBROWSER_AUTO_UPDATE="${CLOAKBROWSER_AUTO_UPDATE:-false}"
mkdir -p "$CLOAKBROWSER_CACHE_DIR"

apt-get update

audio_package="libasound2t64"
if apt-cache policy libasound2 | grep -Eq "Candidate: [^(]"; then
  audio_package="libasound2"
fi

apt-get install -y --no-install-recommends \
  fonts-freefont-ttf \
  fonts-ipafont-gothic \
  fonts-unifont \
  fonts-liberation \
  fonts-noto-color-emoji \
  fonts-tlwg-loma-otf \
  fonts-wqy-zenhei \
  xvfb \
  libatk-bridge2.0-0 \
  libatk1.0-0 \
  libatspi2.0-0 \
  libcairo2 \
  libcups2 \
  libdbus-1-3 \
  libdrm2 \
  libgbm1 \
  libgtk-3-0 \
  libnspr4 \
  libnss3 \
  libpango-1.0-0 \
  libx11-6 \
  libxcb1 \
  libxcomposite1 \
  libxdamage1 \
  libxext6 \
  libxfixes3 \
  libxkbcommon0 \
  libxrandr2 \
  libxrender1 \
  libxshmfence1 \
  "$audio_package"

python -m cloakbrowser install
python -m cloakbrowser update
python -m cloakbrowser info
