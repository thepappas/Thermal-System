#!/bin/sh
# Uses only throwaway credentials and an isolated Podman network.
set -eu
cd "$(dirname "$0")/.."
prefix="hvac-smoke-$$"
network="$prefix-net"
broker="$prefix-broker"
node="$prefix-node"
cleanup() {
  podman rm -f "$node" >/dev/null 2>&1 || :
  podman rm -f "$broker" >/dev/null 2>&1 || :
  podman network rm "$network" >/dev/null 2>&1 || :
}
trap cleanup EXIT HUP INT TERM
podman network create "$network" >/dev/null
podman run -d --name "$broker" --network "$network" --network-alias mosquitto \
  --entrypoint sh docker.io/library/eclipse-mosquitto:2.0.21 -ec '
    cd /mosquitto/config
    printf "smoke-test-only\nsmoke-test-only\n" | mosquitto_passwd -c passwords hvac
    chmod 644 passwords
    printf "listener 1883 0.0.0.0\nallow_anonymous false\npassword_file /mosquitto/config/passwords\nlog_dest stdout\n" > smoke.conf
    exec mosquitto -c smoke.conf
  ' >/dev/null
podman run -d --name "$node" --network "container:$broker" \
  -e MQTT_HOST=127.0.0.1 -e MQTT_PORT=1883 -e MQTT_USER=hvac \
  -e MQTT_PASSWORD=smoke-test-only -e INFLUX_URL=http://influxdb:8086 \
  -e INFLUX_ORG=hvac -e INFLUX_BUCKET=hvac -e INFLUX_TOKEN=smoke-test-only \
  -v "$PWD/nodered/flows.json:/data/flows.json:ro,Z" \
  -v "$PWD/infrastructure/nodered-credentials.json:/data/flows_cred.json:ro,Z" \
  docker.io/nodered/node-red:4.0.9 >/dev/null
attempt=0
while [ "$attempt" -lt 30 ]; do
  if podman logs "$node" 2>&1 | grep -q 'Connected to broker: .*mqtt://127.0.0.1:1883'; then
    if podman exec "$broker" mosquitto_sub -h localhost -t hvac/test -C 1 -W 2 >/dev/null 2>&1; then
      echo "Broker unexpectedly allowed anonymous access" >&2
      exit 1
    fi
    if podman exec "$broker" mosquitto_sub -h localhost -u hvac -P incorrect -t hvac/test -C 1 -W 2 >/dev/null 2>&1; then
      echo "Broker unexpectedly accepted incorrect credentials" >&2
      exit 1
    fi
    echo "Node-RED connected to authenticated Mosquitto using environment credentials."
    exit 0
  fi
  attempt=$((attempt + 1))
  sleep 1
done
echo "Node-RED did not authenticate within 30 seconds:" >&2
podman logs "$node" 2>&1 >&2
podman logs "$broker" 2>&1 >&2
exit 1
