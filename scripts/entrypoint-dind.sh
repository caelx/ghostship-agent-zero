#!/bin/bash
set -euo pipefail

log_file="${DOCKERD_LOG_FILE:-/var/log/ghostship-dockerd.log}"
docker_host="${DOCKER_HOST:-unix:///var/run/docker.sock}"
storage_driver="${DOCKERD_STORAGE_DRIVER:-overlay2}"
data_root="${DOCKERD_DATA_ROOT:-/var/lib/docker}"

export DOCKER_HOST="$docker_host"

mkdir -p "$(dirname "$log_file")" "$data_root" /var/run
rm -f /var/run/docker.pid

if ! docker info >/dev/null 2>&1; then
  dockerd \
    --host="$docker_host" \
    --data-root="$data_root" \
    --storage-driver="$storage_driver" \
    >"$log_file" 2>&1 &
fi

for _ in $(seq 1 60); do
  if docker info >/dev/null 2>&1; then
    exec "$@"
  fi
  sleep 1
done

echo "dockerd did not become ready; recent log output follows:" >&2
tail -n 80 "$log_file" >&2 || true
exit 1
