#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/lib.sh"

echo "checking bw"
run_in_image bw --version
echo "checking fd"
run_in_image fd --version
echo "checking gcloud"
run_in_image gcloud --version
echo "checking gh"
run_in_image gh --version
echo "checking git"
run_in_image git --version
echo "checking gws"
run_in_image gws --version
echo "checking jq"
run_in_image jq --version
echo "checking rg"
run_in_image rg --version
echo "checking tmux"
run_in_image tmux -V
echo "checking uv"
run_in_image uv --version
echo "checking yq"
run_in_image yq --version
