#!/bin/bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y --no-install-recommends \
  apt-transport-https \
  ca-certificates \
  curl \
  fd-find \
  git \
  gnupg \
  jq \
  lsb-release \
  npm \
  ripgrep \
  tmux \
  wget \
  yq

install -d -m 0755 /etc/apt/keyrings

if [ ! -f /etc/apt/keyrings/cloud.google.gpg ]; then
  curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
    | gpg --dearmor -o /etc/apt/keyrings/cloud.google.gpg
  chmod 0644 /etc/apt/keyrings/cloud.google.gpg
fi

cat >/etc/apt/sources.list.d/google-cloud-sdk.list <<'EOF'
deb [signed-by=/etc/apt/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main
EOF

if [ ! -f /etc/apt/keyrings/githubcli-archive-keyring.gpg ]; then
  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    -o /etc/apt/keyrings/githubcli-archive-keyring.gpg
  chmod 0644 /etc/apt/keyrings/githubcli-archive-keyring.gpg
fi

ARCH="$(dpkg --print-architecture)"
cat >/etc/apt/sources.list.d/github-cli.list <<EOF
deb [arch=${ARCH} signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main
EOF

apt-get update
apt-get install -y --no-install-recommends google-cloud-cli gh

npm install -g @bitwarden/cli @googleworkspace/cli

if ! command -v fd >/dev/null 2>&1 && command -v fdfind >/dev/null 2>&1; then
  ln -s /usr/bin/fdfind /usr/local/bin/fd
fi

if ! command -v uv >/dev/null 2>&1; then
  curl -Ls https://astral.sh/uv/install.sh | UV_INSTALL_DIR=/usr/local/bin sh
fi

apt-get clean
rm -rf /var/lib/apt/lists/*
