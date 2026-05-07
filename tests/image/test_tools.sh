#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/lib.sh"

run_in_image bw --version
run_in_image fd --version
run_in_image gcloud --version
run_in_image gh --version
run_in_image git --version
run_in_image gws --version
run_in_image jq --version
run_in_image rg --version
run_in_image tmux -V
run_in_image uv --version
run_in_image yq --version
