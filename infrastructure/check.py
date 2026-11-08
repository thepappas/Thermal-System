#!/usr/bin/env python3
"""Static checks; a running stack still needs the commissioning checks."""
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)


def rendered(*files, env=None):
    command = ["docker", "compose"]
    for path in files:
        command.extend(["-f", path])
    command.extend(["config", "--format", "json"])
    return json.loads(subprocess.check_output(command, env=env))


base = "infrastructure/compose.yml"
dev = "infrastructure/compose.dev.yml"
prod = rendered(base)
services = prod["services"]
assert set(services) == {"mosquitto", "influxdb", "nodered", "grafana"}
for name, port in (("mosquitto", 1883), ("nodered", 1880), ("influxdb", 8086), ("grafana", 3000)):
    mapping = services[name]["ports"]
    assert len(mapping) == 1 and mapping[0]["host_ip"] == "127.0.0.1"
    assert mapping[0]["target"] == port
assert services["nodered"]["environment"]["MQTT_HOST"] == "mosquitto"
assert services["nodered"]["environment"]["MQTT_PORT"] == "1883"
assert services["nodered"]["environment"]["MQTT_USER"] == "hvac"
assert services["nodered"]["environment"]["MQTT_USERNAME"] == "hvac"
assert services["nodered"]["environment"]["INFLUX_URL"] == "http://influxdb:8086"
assert services["nodered"]["environment"]["INFLUX_ORG"] == "hvac"
assert services["nodered"]["environment"]["INFLUX_BUCKET"] == "hvac"
assert any(mount["target"] == "/data/flows.json" and mount["read_only"]
           for mount in services["nodered"]["volumes"])
assert json.loads(Path("infrastructure/nodered-credentials.json").read_text()) == {
    "broker": {"user": "${MQTT_USER}", "password": "${MQTT_PASSWORD}"}
}
assert services["influxdb"]["environment"]["DOCKER_INFLUXDB_INIT_ORG"] == "hvac"
assert services["influxdb"]["environment"]["DOCKER_INFLUXDB_INIT_BUCKET"] == "hvac"
assert services["grafana"]["environment"]["GF_AUTH_ANONYMOUS_ENABLED"] == "false"
assert "allow_anonymous false" in Path("infrastructure/mosquitto/mosquitto.conf").read_text()

env = dict(os.environ, MQTT_BIND_IP="192.0.2.1", NODERED_BIND_IP="192.0.2.1",
           INFLUX_BIND_IP="192.0.2.1", GRAFANA_BIND_IP="192.0.2.1")
development = rendered(base, dev, env=env)
for name in ("mosquitto", "nodered", "influxdb", "grafana"):
    assert all(port["host_ip"] == "127.0.0.1" for port in development["services"][name]["ports"])
tools = rendered(base, env=dict(os.environ, COMPOSE_PROFILES="tools"))
assert tools["services"]["esphome"]["image"] == "ghcr.io/esphome/esphome:2025.10.3"

flows = json.loads(Path("nodered/flows.json").read_text())
assert any(node.get("id") == "broker" and node.get("type") == "mqtt-broker" for node in flows)
writer = next(node for node in flows if node.get("name") == "Validate and encode observations")
fields = set(re.findall(r"'hvac/[^']+':'([^']+)'", writer["func"]))
assert fields, "could not find writer field mapping"
dashboards = list(Path("grafana/dashboards").glob("*.json"))
assert {path.stem for path in dashboards} == {"overview", "roof", "mass", "operations", "twin"}
for path in dashboards:
    dashboard = json.loads(path.read_text())
    assert dashboard["uid"] and dashboard["panels"]
    for panel in dashboard["panels"]:
        for target in panel.get("targets", []):
            query = target["query"]
            assert 'bucket: "hvac"' in query and 'r._measurement == "hvac"' in query
            match = re.search(r'r\._field == "([^"]+)"', query)
            if match:
                assert match.group(1) in fields, (path, match.group(1))
            match = re.search(r'r\._field =~ /\^\(([^)]+)\)\$/', query)
            if match:
                assert set(match.group(1).split("|")) <= fields, path
print("Static infrastructure and telemetry checks passed.")
