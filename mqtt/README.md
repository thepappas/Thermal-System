# MQTT namespace and contract

The broker is local (`mosquitto` when resolvable by the ESP32, otherwise its
configured LAN IP/name). Provision distinct authenticated node accounts and
least-privilege ACLs on the broker; this directory does not configure or start a
broker. The ESPHome examples disable discovery. See
[node setup and wiring](../esphome/README.md).

## Observations

Each topic carries a UTF-8 numeric temperature in °C, published approximately
every 30 seconds, QoS 0, **not retained**. A missing, non-numeric, non-finite,
implausible, or stale value must be treated as invalid, not as zero. Each topic
has exactly one intended publisher; don't publish a replacement reading under
the same topic without explicitly changing its owner.

| Topic | Owner | Physical measurement |
| --- | --- | --- |
| `hvac/roof/temp_in` | roof | Roof inlet |
| `hvac/roof/temp_out` | roof | Roof outlet |
| `hvac/outdoor/temp` | roof | Outdoor air |
| `hvac/house/temp_supply` | mechanical | House supply air |
| `hvac/house/temp_return` | mechanical | House return air |
| `hvac/mass/temp_in` | mechanical | Thermal mass inlet |
| `hvac/mass/temp_out` | mechanical | Thermal mass outlet |
| `hvac/core/temp` | expansion | Separate external core sensor |

These are observations, not proof of airflow, damper position, or a functioning
safety system. Timestamp readings at receipt and set a site-validated freshness
deadline for **each** measurement; node availability is not sensor validity.

## Availability

`hvac/status/roof`, `hvac/status/mechanical`, and `hvac/status/expansion`
contain `online` or `offline`. Each node publishes retained `online` on MQTT
connection, and `offline` as its retained last will or graceful shutdown
message. An unexpected disconnect is detected only after the broker's MQTT
keepalive timeout; retained `online` can also be stale after broker failure or
restart. Consumers must require both a live broker connection and recent
measurements, and fail closed on unknown status or missing/stale readings.
Availability is informational, not an independent hardware watchdog.

## Commands and Shelly

There are **no command topics** in these monitoring templates. Do not publish
retained commands, including for any future damper or Shelly integration; clear
existing retained command messages at the broker before commissioning. Broker
ACLs should deny node access outside their own telemetry/status and prevent
unapproved command publishers. If control is designed later, document exact
topics, owners, permissions, payloads, and fail-safe behavior before use; no
command should bypass physical interlocks. Shelly topics and MQTT capabilities
are model/firmware-specific and must be verified against the device; relay state
and power are not proof of airflow.
