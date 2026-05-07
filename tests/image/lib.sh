#!/bin/bash
set -euo pipefail

image="${1:-}"

if [ -z "$image" ]; then
  echo "usage: $0 IMAGE" >&2
  exit 2
fi

run_in_image() {
  docker run --rm "$image" "$@"
}

run_bash_in_image() {
  docker run --rm "$image" bash -lc "$1"
}

run_xvfb_bash_in_image() {
  docker run --rm "$image" xvfb-run -a bash -lc "$1"
}
