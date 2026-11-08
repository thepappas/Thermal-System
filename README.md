# Thermal System

Local-first monitoring and staged control of a residential air-based thermal
battery. **Monitor first; automate only after site-specific commissioning.**
This repository is a reference implementation, not a certified safety control.
Do not connect actuators until the hazards and interlocks in
[safety](docs/safety.md) have been reviewed by qualified personnel.

## Current scope

The supplied Node-RED flow is **monitoring and advisory only**: it does not
command dampers or the blower. Its thresholds are examples, not commissioned
operating settings. The ESPHome templates do not implement a complete actuator
control system. Dashboard state and digital-twin panels are incomplete where
no suitable measured input exists. Hardware interlocks, verified airflow,
seasonal logic, alarms, feedback, and a validated control implementation are
required before unattended automation.

## Start here

1. Read [architecture](docs/architecture.md), [safety](docs/safety.md), and
   [wiring](wiring/README.md).
2. Follow [deployment and commissioning](docs/operations.md).
3. Use [MQTT topics](mqtt/README.md) to identify every measurement and owner.
4. Review the [digital twin](digital-twin/README.md) before interpreting energy
   or state-of-charge estimates.

No cloud service is required for operation. Initial installation and updates
require access to container images and firmware dependencies; mirror these
locally for offline recovery.

## Repository map

| Path | Purpose |
| --- | --- |
| `infrastructure/` | Podman Compose deployment |
| `esphome/` | ESP32 configuration templates |
| `mqtt/` | Broker configuration and topic contract |
| `nodered/` | Local control and telemetry flows |
| `grafana/` | Datasource and dashboards |
| `influxdb/` | Historical storage notes |
| `wiring/`, `diagrams/` | Physical and logical design |
| `scripts/`, `tests/` | Operational and validation tools |
| `digital-twin/` | Model and engineering assumptions |
| `examples/` | Site-specific configuration examples |

Temperatures are in °C, power in W, current in A, and time is UTC unless
explicitly stated otherwise. See [operations](docs/operations.md) for backup,
upgrade, and recovery procedures.

For isolated development, `python3 scripts/mqtt_simulator.py --host HOST`
publishes synthetic readings on the real HVAC topic names. **Never point it at
the production broker**: its data is indistinguishable from live observations.
Set `MQTT_USER` and `MQTT_PASSWORD` in the environment when authentication is
required. See [Node-RED](nodered/README.md) for the advisory state machine.
