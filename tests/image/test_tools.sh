#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/lib.sh"

check() {
  echo "checking $1"
  shift
  run_in_image "$@"
}

check_bash() {
  echo "checking $1"
  shift
  run_bash_in_image "$*"
}

check gh gh --version
check git git --version
check openssh-client ssh -V

check curl curl --version
check wget wget --version
check_bash ca-certificates 'test -s /etc/ssl/certs/ca-certificates.crt'

check jq jq --version
check yq yq --version
check rg rg --version
check fd fd --version

check python3 python3 --version
check pip pip --version
check uv uv --version
check nodejs node --version
check_bash nodejs-22 'test "$(node -p "process.versions.node.split(\".\")[0]")" -ge 22'
check npm npm --version
check npx npx --version
check corepack corepack --version
check nix nix --extra-experimental-features "nix-command flakes" flake --help
check make make --version
check just just --version

check bash bash --version
check tar tar --version
check gzip gzip --version
check xz xz --version
check zstd zstd --version
check zip zip -v
check unzip unzip -v
check_bash 7zip 'command -v 7z >/dev/null || command -v 7zz >/dev/null'
check file file --version
check less less --version
check tree tree --version
check tmux tmux -V

check pre-commit pre-commit --version
check gitleaks gitleaks version
check trufflehog trufflehog --version
check_bash git-secrets 'command -v git-secrets >/dev/null && git secrets --scan --no-index /dev/null >/dev/null'
check git-filter-repo git-filter-repo --version

check shellcheck shellcheck --version
check shfmt shfmt --version
check actionlint actionlint --version

check_bash GH_PROMPT_DISABLED 'test "${GH_PROMPT_DISABLED:-}" = "1"'
check_bash no-custom-runtime-env '! env | grep -E "^(A0_RUNTIME_ROOT|XDG_CONFIG_HOME|XDG_DATA_HOME|XDG_STATE_HOME|XDG_CACHE_HOME|XDG_RUNTIME_DIR|GH_CONFIG_DIR|GIT_CONFIG_GLOBAL|RIPGREP_CONFIG_PATH|BITWARDENCLI_APPDATA_DIR)="'
check_bash no-custom-runtime-dir 'test ! -e /a0/usr/.runtime'
