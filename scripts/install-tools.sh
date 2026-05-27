#!/bin/bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

usage() {
  echo "usage: install-tools.sh {apt|npm|uv|github|nix|docker|all}" >&2
}

refresh_apt_lists() {
  for source_file in /etc/apt/sources.list /etc/apt/sources.list.d/*; do
    [ -f "$source_file" ] || continue
    sed -i \
      -e 's|http://http.kali.org/kali|http://kali.download/kali|g' \
      -e 's|https://http.kali.org/kali|http://kali.download/kali|g' \
      "$source_file"
  done
  rm -rf /var/lib/apt/lists/*
  mkdir -p /var/lib/apt/lists/partial
  apt-get update
}

install_apt_tools() {
  refresh_apt_lists
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

  refresh_apt_lists

  archive_package="p7zip-full"
  if apt-cache show 7zip >/dev/null 2>&1; then
    archive_package="7zip"
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
    git-secrets \
    gitleaks \
    gzip \
    jq \
    just \
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
    shfmt \
    tar \
    tmux \
    tree \
    unzip \
    wget \
    xz-utils \
    yq \
    zip \
    zstd \
    "$archive_package"

  if ! command -v fd >/dev/null 2>&1 && command -v fdfind >/dev/null 2>&1; then
    ln -s /usr/bin/fdfind /usr/local/bin/fd
  fi
  if ! command -v pip >/dev/null 2>&1 && command -v pip3 >/dev/null 2>&1; then
    ln -s "$(command -v pip3)" /usr/local/bin/pip
  fi

  apt-get purge -y gnupg
}

install_npm_tools() {
  if ! npm view npm version >/dev/null 2>&1; then
    install_official_nodejs
  fi
  npm view npm version >/dev/null
  npm config set prefix /usr/local
  if ! command -v corepack >/dev/null 2>&1; then
    npm install -g corepack
  fi
  corepack enable || true
}

install_official_nodejs() {
  arch="$(dpkg --print-architecture)"
  case "$arch" in
    amd64)
      node_arch="x64"
      ;;
    arm64)
      node_arch="arm64"
      ;;
    *)
      echo "unsupported Node.js architecture: $arch" >&2
      exit 1
      ;;
  esac

  tmp="$(mktemp -d)"
  base_url="https://nodejs.org/dist/latest-v22.x"
  checksums="$tmp/SHASUMS256.txt"
  curl -fsSLo "$checksums" "$base_url/SHASUMS256.txt"
  tarball="$(awk -v arch="linux-${node_arch}.tar.xz" '$2 ~ arch "$" { print $2; exit }' "$checksums")"
  if [ -z "$tarball" ]; then
    echo "could not find Node.js linux-${node_arch} tarball" >&2
    exit 1
  fi
  curl -fsSLo "$tmp/$tarball" "$base_url/$tarball"
  (cd "$tmp" && grep "  $tarball$" SHASUMS256.txt | sha256sum -c -)

  rm -rf /opt/nodejs
  mkdir -p /opt/nodejs
  tar -xJf "$tmp/$tarball" -C /opt/nodejs --strip-components=1
  ln -sf /opt/nodejs/bin/node /usr/local/bin/node
  ln -sf /opt/nodejs/bin/npm /usr/local/bin/npm
  ln -sf /opt/nodejs/bin/npx /usr/local/bin/npx
  ln -sf /opt/nodejs/bin/corepack /usr/local/bin/corepack
  rm -rf "$tmp"
  hash -r
}

install_uv() {
  if ! command -v uv >/dev/null 2>&1; then
    curl -Ls https://astral.sh/uv/install.sh | UV_INSTALL_DIR=/usr/local/bin sh
  fi
}

install_github_tools() {
  /tmp/ghostship/install-github-tools.py
}

install_nix() {
  if ! command -v nix >/dev/null 2>&1; then
    export NIX_CONFIG="filter-syscalls = false"
    tmp="$(mktemp -d)"
    trap 'rm -rf "$tmp"' EXIT
    curl --http1.1 --proto '=https' --tlsv1.2 -fsSL \
      --retry 5 --retry-all-errors --retry-delay 2 \
      -o "$tmp/determinate-nix-installer.sh" \
      https://install.determinate.systems/nix
    sh "$tmp/determinate-nix-installer.sh" install linux --no-confirm --init none
    rm -rf "$tmp"
    trap - EXIT
  fi

  mkdir -p /etc/nix
  cat >/etc/nix/nix.conf <<'EOF'
experimental-features = nix-command flakes
filter-syscalls = false
EOF
}

install_docker() {
  refresh_apt_lists
  apt-get install -y --no-install-recommends ca-certificates curl gnupg

  . /etc/os-release
  docker_repo_id="${DOCKER_APT_REPO_ID:-${ID:-debian}}"
  docker_codename="${DOCKER_APT_CODENAME:-${VERSION_CODENAME:-bookworm}}"
  case "$docker_repo_id" in
    debian|ubuntu)
      ;;
    kali)
      docker_repo_id="debian"
      docker_codename="${DOCKER_APT_CODENAME:-bookworm}"
      ;;
    *)
      echo "unsupported Docker apt repository OS: $docker_repo_id" >&2
      exit 1
      ;;
  esac

  install -d -m 0755 /etc/apt/keyrings
  if [ ! -f /etc/apt/keyrings/docker.asc ]; then
    curl -fsSL "https://download.docker.com/linux/${docker_repo_id}/gpg" \
      -o /etc/apt/keyrings/docker.asc
    chmod 0644 /etc/apt/keyrings/docker.asc
  fi

  arch="$(dpkg --print-architecture)"
  cat >/etc/apt/sources.list.d/docker.list <<EOF
deb [arch=${arch} signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/${docker_repo_id} ${docker_codename} stable
EOF

  refresh_apt_lists
  apt-get install -y --no-install-recommends \
    containerd.io \
    docker-buildx-plugin \
    docker-ce \
    docker-ce-cli \
    docker-compose-plugin
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
  docker)
    install_docker
    ;;
  all)
    install_apt_tools
    install_npm_tools
    install_uv
    install_github_tools
    install_nix
    install_docker
    ;;
  *)
    usage
    exit 2
    ;;
esac
