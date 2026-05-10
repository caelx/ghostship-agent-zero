#!/bin/bash
set -euo pipefail

image="${1:-}"

if [ -z "$image" ]; then
  echo "usage: tests/run-image-tests.sh IMAGE" >&2
  exit 2
fi

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$root/tests/image/test_provider_plugins.sh" "$image"
"$root/tests/image/test_tools.sh" "$image"
"$root/tests/image/test_cloakbrowser.sh" "$image"
