#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if [ "$#" -ne 1 ] || [ ! -f "$1/FORMAT" ] || [ "$(cat "$1/FORMAT")" != thermal-stack-backup-v1 ]; then
  echo "Usage: $0 TRUSTED_BACKUP_DIRECTORY" >&2
  exit 2
fi
source_dir=$(cd "$1" && pwd)
volumes="thermal_mosquitto-data thermal_influx-data thermal_influx-config thermal_nodered-data thermal_grafana-data"
[ ! -e data/secrets ] || { echo "Refusing to overwrite data/secrets" >&2; exit 1; }
[ -f "$source_dir/secrets.tar" ] || { echo "Missing secrets archive" >&2; exit 1; }
for volume in $volumes; do
  [ -f "$source_dir/$volume.tar" ] || { echo "Missing $volume archive" >&2; exit 1; }
  if podman volume exists "$volume"; then
    echo "Refusing to overwrite volume $volume" >&2; exit 1
  fi
done
umask 077
mkdir -p data
tar -C data -xf "$source_dir/secrets.tar"
for volume in $volumes; do
  podman volume create "$volume" >/dev/null
  podman volume import "$volume" "$source_dir/$volume.tar"
done
echo "Restore complete. Start the stack and verify data, credentials, and safe state."
