# Operations and commissioning

This is monitoring/advisory software, **not a safety system**. Keep independent
physical interlocks and the legacy control in place. Confirm the safe state on
restart and loss of power/network before connecting any actuator; see
`docs/safety.md`. Never treat missing telemetry, a relay command, or a dashboard
as proof of airflow or damper position.

## Host and network

Install Podman and a Compose provider. These examples use `podman compose`
with Docker Compose v2.24.4 or newer (the development override uses
`!override`); other providers may not support it. Run from the repository root.
Use one dedicated host account and a reliable filesystem. Configure automatic
Podman service startup/lingering using your distribution's facilities and test
after a real reboot; `restart: unless-stopped` alone is not a boot service.
Images are version-tagged, not digest-pinned; review advisories and pin trusted
digests in your deployment before production.

By default all published ports bind to 127.0.0.1: MQTT 1883, Node-RED 1880,
InfluxDB 8086 and Grafana 3000. Use SSH local forwarding for administration.
To let devices reach MQTT, set `MQTT_BIND_IP` to the host's *specific* HVAC LAN
address, e.g. `export MQTT_BIND_IP=192.168.10.2`, and allow TCP 1883 only from
the HVAC subnet in the host firewall. Configure the devices with that LAN
address; **inside** the stack the broker hostname is `mosquitto`. Never use
`0.0.0.0` or publish ports to the Internet. MQTT here has password authentication
but **no TLS**: credentials and telemetry are plaintext. Use a physically
isolated trusted network or an authenticated encrypted tunnel; do not rely on
the password for confidentiality. All devices share one account; it has full
topic access, so do not connect untrusted clients.

Grafana, InfluxDB, and the Node-RED editor require authentication, but HTTP is
plaintext. Keep their default loopback binds and access them through SSH or a
properly secured TLS reverse proxy with access controls; merely changing their
bind IP exposes credentials on the LAN. ESPHome is an on-demand CLI tool, not
an unauthenticated dashboard. Do not mount USB devices or enable privileged
containers without reviewing the implications.

## First boot and secrets

The `data/` directory is git-ignored; never commit its contents. Secrets are
separate bind-mounted files, readable by container UIDs and accessible on the
host only through the private directory. Container/host administrators can
still read them. Host backups and the Podman data store contain credentials.
The setup uses `openssl`, Python 3 and the container images. Secure the host,
terminal and shell history; don't paste secrets into commands or share logs.

1. Make a private secret directory and generate independent random values:

   ```sh
   umask 077
   mkdir -p data/secrets
   chmod 700 data/secrets
   printf '%s\n' admin > data/secrets/influx-user
   for name in influx-password influx-admin-token mqtt-password grafana-password nodered-credential-secret; do
     openssl rand -hex 32 > "data/secrets/$name"
   done
   { cat data/secrets/mqtt-password; cat data/secrets/mqtt-password; } |
     podman run --rm -i -v "$PWD/data/secrets:/secrets:Z" \
       --entrypoint mosquitto_passwd docker.io/library/eclipse-mosquitto:2.0.21 \
       -c /secrets/mosquitto.passwd hvac
   ```

2. Generate an independent Node-RED editor password hash interactively:

   ```sh
   podman run --rm -it --entrypoint node-red docker.io/nodered/node-red:4.0.9 admin hash-pw
   ```

   Enter a strong password; privately copy only the resulting bcrypt hash into
   `data/secrets/nodered-admin-hash`, followed by a newline. Store the editor
   password in a password manager. Its user is `admin`.

3. Make the individual files readable by the unprivileged container users
   while keeping the parent directory private, then initialize the database:

   ```sh
   chmod 644 data/secrets/*
   podman compose -f infrastructure/compose.yml up -d mosquitto influxdb
   podman compose -f infrastructure/compose.yml logs influxdb
   ```

   Wait for initial setup to finish before proceeding. Setup happens **only**
   on an empty Influx volume. Changing initialization files later does not
   rotate existing database credentials. The initial org and bucket are both
   `hvac` and the username is `admin`.

4. Create separate bucket-scoped Influx tokens for the writer and Grafana
   reader. The commands below briefly pass the admin token to a local process;
   run only on a trusted host where other users cannot inspect processes.

   ```sh
   bucket=$(podman compose -f infrastructure/compose.yml exec -T influxdb \
     influx bucket list --org hvac --name hvac --token "$(cat data/secrets/influx-admin-token)" --json \
     | python3 -c 'import json,sys; print(json.load(sys.stdin)[0]["id"])')
   podman compose -f infrastructure/compose.yml exec -T influxdb \
     influx auth create --org hvac --write-bucket "$bucket" --token "$(cat data/secrets/influx-admin-token)" --json \
     | python3 -c 'import json,sys; print(json.load(sys.stdin)["token"])' > data/secrets/nodered-influx-token
   podman compose -f infrastructure/compose.yml exec -T influxdb \
     influx auth create --org hvac --read-bucket "$bucket" --token "$(cat data/secrets/influx-admin-token)" --json \
     | python3 -c 'import json,sys; print(json.load(sys.stdin)["token"])' > data/secrets/grafana-influx-token
   chmod 644 data/secrets/nodered-influx-token data/secrets/grafana-influx-token
   ```

   Check both files are nonempty before continuing. Token values are made
   available as process environment variables to Node-RED and Grafana for
   integration with their existing configuration mechanisms.

5. Start services:

   ```sh
   podman compose -f infrastructure/compose.yml up -d
   podman compose -f infrastructure/compose.yml ps
   podman compose -f infrastructure/compose.yml logs --tail=50
   ```

   Log in to Node-RED at `http://127.0.0.1:1880` with the editor credentials.
   The flow is mounted read-only at `/data/flows.json`; review changes in the
   repository and recreate the container to apply them. Editor deployments
   cannot persist to this mount. The mounted credentials file contains only
   environment references, not passwords, for the broker node ID `broker`.
   Node-RED may warn that this file is unencrypted; it contains no secret
   values. Keep its node ID synchronized with the flow. Set username `hvac`
   and the password from `data/secrets/mqtt-password` on devices.

   The flow receives `MQTT_HOST=mosquitto`, `MQTT_PORT=1883`,
   `MQTT_USER=hvac` (also available as `MQTT_USERNAME`), `MQTT_PASSWORD`
   from the mounted secret,
   `INFLUX_URL=http://influxdb:8086`, `INFLUX_ORG=hvac`,
   `INFLUX_BUCKET=hvac`, and `INFLUX_TOKEN` from the writer-token file.
   The two secret values exist in the Node-RED process environment.
   Node-RED substitutes `${MQTT_USER}` and `${MQTT_PASSWORD}` in its broker
   credentials at startup. Keep both username variables consistent if
   changing the account.

   Log in to Grafana at `http://127.0.0.1:3000` as `admin` with
   `data/secrets/grafana-password`. Find the provisioned HVAC dashboards.
   Grafana's initial admin password file only applies to a fresh Grafana
   database. Change/rotate it using Grafana's supported admin procedure.
   Check Influx write errors in Node-RED logs and verify live data and each
   dashboard. There are no preconfigured alert rules. The controller flow does
   not queue telemetry through outages.

The Compose stack defines no service health checks. `depends_on` orders
container startup only; it does not wait for service readiness or prove MQTT,
Influx writes, or sensor freshness. Check logs and perform end-to-end
commissioning after startup; telemetry during database outages can be lost.

For local development, append `-f infrastructure/compose.dev.yml` to the
Compose commands. It forces loopback bindings even if LAN bind variables are
set, but uses the **same volumes and credentials**; it is not an isolated
test environment. For ESPHome, run e.g.
`podman compose -f infrastructure/compose.yml run --rm esphome version`;
the image is ESPHome 2025.10.3 and the repository `esphome/` directory is
mounted at `/config`. Host firmware build directories are
`esphome/.esphome/build/thermal-roof/`, `thermal-mechanical/`, and
`thermal-expansion/`; PlatformIO outputs are in each directory's
`.pioenvs/<node-name>/`, including `firmware.bin`. Choose the correct
factory/OTA image for the actual board. See the ESPHome README for
configuration, firmware secrets and OTA precautions.

## CI and local checks

With Python 3, Node.js, Podman, Docker Compose v2.24.4+ as its Compose provider,
and registry access, run from the repository root:

```sh
podman compose -f infrastructure/compose.yml -f infrastructure/compose.dev.yml config --quiet
python3 infrastructure/check.py
node --check infrastructure/nodered-settings.js
sh -n scripts/backup.sh scripts/backup-restore.sh infrastructure/smoke-node-red.sh
infrastructure/smoke-node-red.sh
```

The smoke test pulls the pinned Mosquitto and Node-RED images if necessary,
uses throwaway credentials and an isolated shared network namespace, verifies
authenticated Node-RED connection and anonymous rejection, and removes its
containers and network. It does not test the Compose network's `mosquitto`
DNS, the full stack, or backup restoration. No real secrets or first-boot
database are needed for these checks.

## Backup, restore and upgrade

Stop the stack with `podman compose -f infrastructure/compose.yml stop` and
ensure no other containers use its volumes. Then run
`scripts/backup.sh backups/$(date -u +%Y%m%dT%H%M%SZ)`; the destination must
not already exist. This takes offline, consistent volume exports and a secrets
archive. Back up the repository and site-specific ESPHome configuration
separately. Backups contain plaintext credentials and sensitive telemetry:
encrypt them, restrict access, keep an offline copy, and test recovery.
Restart with `podman compose -f infrastructure/compose.yml up -d`.

To restore, use only a trusted archive (tar extraction is not safe for
untrusted input). On a clean host with the same project name and compatible
images, restore the repository/site configuration first. With the stack
stopped and `data/secrets` and all five `thermal_*` volumes absent, run
`scripts/backup-restore.sh BACKUP_DIRECTORY`; it refuses to overwrite existing
data. If a restore fails partway, inspect and remove only the volumes and
secrets created by that attempt before retrying. Start the stack and verify
logins, database history, MQTT authentication, flow state, and physical safe
state. The restore includes Influx metadata and tokens: do not run first-boot
initialization again.

Before upgrading images or flows, take and test an offline backup, record
versions, review release notes and compatibility, then pull and recreate one
service at a time. Observe logs and confirm telemetry and fail-safe behavior.
Keep old images and backups for rollback. Rotating MQTT requires updating the
password file, device credentials and Node-RED together, then restarting the
broker; rotating Influx tokens requires updating consumers and revoking the old
tokens. Restart the affected containers after changing secret files.
