#!/bin/bash
set -euo pipefail

image="${1:-}"

if [ -z "$image" ]; then
  echo "usage: $0 IMAGE" >&2
  exit 2
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

cat >"$tmp/Dockerfile" <<'EOF'
FROM docker.io/library/busybox:latest
COPY message.txt /message.txt
CMD ["cat", "/message.txt"]
EOF

cat >"$tmp/message.txt" <<'EOF'
ghostship-dind-ok
EOF

timeout 180s docker run --rm --privileged --shm-size=2g \
  -v "$tmp:/tmp/dind-smoke:ro" \
  "$image" \
  bash -lc '
    set -euo pipefail
    test "${DOCKER_HOST:-}" = "unix:///var/run/docker.sock"
    test ! -S /host/var/run/docker.sock
    docker info >/dev/null
    docker build -t ghostship-dind-smoke:local /tmp/dind-smoke
    test "$(docker run --rm ghostship-dind-smoke:local)" = "ghostship-dind-ok"
  '
