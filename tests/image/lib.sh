#!/bin/bash
set -euo pipefail

image="${1:-}"

if [ -z "$image" ]; then
  echo "usage: $0 IMAGE" >&2
  exit 2
fi

run_in_image() {
  local entrypoint="$1"
  shift
  timeout 120s docker run --rm --shm-size=2g --entrypoint "$entrypoint" "$image" "$@"
}

run_bash_in_image() {
  timeout 120s docker run --rm --shm-size=2g --entrypoint bash "$image" -lc "$1"
}
