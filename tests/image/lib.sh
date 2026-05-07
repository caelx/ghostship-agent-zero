#!/bin/bash
set -euo pipefail

image="${1:-}"

if [ -z "$image" ]; then
  echo "usage: $0 IMAGE" >&2
  exit 2
fi

run_in_image() {
  timeout 120s docker run --rm "$image" "$@"
}

run_bash_in_image() {
  timeout 120s docker run --rm "$image" bash -lc "$1"
}

run_xvfb_bash_in_image() {
  timeout 180s docker run --rm "$image" xvfb-run -a -s "-screen 0 1920x1080x24" bash -lc "$1"
}
