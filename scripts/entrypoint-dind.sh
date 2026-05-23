#!/bin/bash
set -euo pipefail

log_file="${DOCKERD_LOG_FILE:-/var/log/ghostship-dockerd.log}"
docker_host="${DOCKER_HOST:-unix:///var/run/docker.sock}"
storage_driver="${DOCKERD_STORAGE_DRIVER:-overlay2}"
data_root="${DOCKERD_DATA_ROOT:-/var/lib/docker}"
allow_storage_fallback="${DOCKERD_STORAGE_FALLBACK:-true}"

export DOCKER_HOST="$docker_host"

mkdir -p "$(dirname "$log_file")" "$data_root" /var/run
rm -f /var/run/docker.pid

start_dockerd() {
  local driver="$1"
  dockerd \
    --host="$docker_host" \
    --data-root="$data_root" \
    --storage-driver="$driver" \
    >"$log_file" 2>&1 &
}

wait_for_dockerd() {
  for _ in $(seq 1 60); do
    if docker info >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  return 1
}

if ! docker info >/dev/null 2>&1; then
  start_dockerd "$storage_driver"
fi

if wait_for_dockerd; then
  exec "$@"
fi

if [ "$storage_driver" = "overlay2" ] && [ "$allow_storage_fallback" = "true" ]; then
  if grep -Eq "failed to mount overlay|driver not supported: overlay2|invalid argument" "$log_file"; then
    echo "dockerd overlay2 storage failed; retrying with vfs storage driver" >&2
    pkill -TERM -x dockerd >/dev/null 2>&1 || true
    pkill -TERM -x containerd >/dev/null 2>&1 || true
    sleep 2
    pkill -KILL -x dockerd >/dev/null 2>&1 || true
    pkill -KILL -x containerd >/dev/null 2>&1 || true
    rm -f /var/run/docker.pid
    start_dockerd vfs
    if wait_for_dockerd; then
      exec "$@"
    fi
  fi
fi

echo "dockerd did not become ready; recent log output follows:" >&2
tail -n 80 "$log_file" >&2 || true
exit 1
