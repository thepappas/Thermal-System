#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 NEW_BACKUP_DIRECTORY" >&2
  exit 2
fi
volumes="thermal_mosquitto-data thermal_influx-data thermal_influx-config thermal_nodered-data thermal_grafana-data"
for volume in $volumes; do
  podman volume exists "$volume" || { echo "Missing volume: $volume" >&2; exit 1; }
  [ -z "$(podman ps -q --filter "volume=$volume")" ] || {
    echo "Stop the stack before backup: $volume is in use" >&2; exit 1;
  }
done
[ -d data/secrets ] || { echo "Missing data/secrets" >&2; exit 1; }
umask 077
mkdir -m 700 -- "$1"
destination=$(cd "$1" && pwd)
for volume in $volumes; do
  podman volume export "$volume" > "$destination/$volume.tar"
done
tar -C data -cf "$destination/secrets.tar" secrets
printf '%s\n' "thermal-stack-backup-v1" > "$destination/FORMAT"
echo "Backup complete: $destination (contains secrets; encrypt before transfer)"
