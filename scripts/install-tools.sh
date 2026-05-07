#!/bin/bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

usage() {
  echo "usage: install-tools.sh {apt|npm|uv|github|nix|all}" >&2
}

install_apt_tools() {
  apt-get update
  apt-get install -y --no-install-recommends ca-certificates curl gnupg

  install -d -m 0755 /etc/apt/keyrings
  if [ ! -f /etc/apt/keyrings/githubcli-archive-keyring.gpg ]; then
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
      -o /etc/apt/keyrings/githubcli-archive-keyring.gpg
    chmod 0644 /etc/apt/keyrings/githubcli-archive-keyring.gpg
  fi

  arch="$(dpkg --print-architecture)"
  cat >/etc/apt/sources.list.d/github-cli.list <<EOF
deb [arch=${arch} signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main
EOF

  apt-get update

  archive_package="p7zip-full"
  if apt-cache show 7zip >/dev/null 2>&1; then
    archive_package="7zip"
  fi

  just_package=()
  if apt-cache show just >/dev/null 2>&1; then
    just_package=(just)
  fi

  apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    curl \
    fd-find \
    file \
    gh \
    git \
    git-filter-repo \
    gzip \
    jq \
    less \
    make \
    nodejs \
    npm \
    openssh-client \
    pre-commit \
    python3 \
    python3-pip \
    ripgrep \
    shellcheck \
    tar \
    tmux \
    tree \
    unzip \
    wget \
    xz-utils \
    yq \
    zip \
    zstd \
    "$archive_package" \
    "${just_package[@]}"

  if ! command -v fd >/dev/null 2>&1 && command -v fdfind >/dev/null 2>&1; then
    ln -s /usr/bin/fdfind /usr/local/bin/fd
  fi
  if ! command -v pip >/dev/null 2>&1 && command -v pip3 >/dev/null 2>&1; then
    ln -s "$(command -v pip3)" /usr/local/bin/pip
  fi

  apt-get purge -y --auto-remove gnupg
}

install_npm_tools() {
  npm install -g @bitwarden/cli
  if ! command -v corepack >/dev/null 2>&1; then
    npm install -g corepack
  fi
  corepack enable || true
}

install_uv() {
  if ! command -v uv >/dev/null 2>&1; then
    curl -Ls https://astral.sh/uv/install.sh | UV_INSTALL_DIR=/usr/local/bin sh
  fi
}

install_github_tools() {
  /tmp/ghostship/install-github-tools.py
  if ! command -v git-secrets >/dev/null 2>&1; then
    tmpdir="$(mktemp -d)"
    git clone --depth 1 https://github.com/awslabs/git-secrets.git "$tmpdir/git-secrets"
    make -C "$tmpdir/git-secrets" install PREFIX=/usr/local
    rm -rf "$tmpdir"
  fi
}

install_nix() {
  if ! command -v nix >/dev/null 2>&1; then
    export NIX_CONFIG="filter-syscalls = false"
    curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix \
      | sh -s -- install linux --no-confirm --init none
  fi

  mkdir -p /etc/nix
  cat >/etc/nix/nix.conf <<'EOF'
experimental-features = nix-command flakes
filter-syscalls = false
EOF
}

case "${1:-all}" in
  apt)
    install_apt_tools
    ;;
  npm)
    install_npm_tools
    ;;
  uv)
    install_uv
    ;;
  github)
    install_github_tools
    ;;
  nix)
    install_nix
    ;;
  all)
    install_apt_tools
    install_npm_tools
    install_uv
    install_github_tools
    install_nix
    ;;
  *)
    usage
    exit 2
    ;;
esac
