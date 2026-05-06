#!/bin/bash
set -euo pipefail

. "/ins/setup_venv.sh" "$@"
. "/ins/copy_A0.sh" "$@"

/opt/ghostship/apply-overlay.sh

echo "Starting A0 bootstrap manager..."
exec python /exe/self_update_manager.py docker-run-ui
