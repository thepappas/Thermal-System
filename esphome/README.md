# ESPHome monitoring nodes

These are ESP32 DevKit (`esp32dev`) templates, not a safety controller.
Read [safety](../docs/safety.md) and [wiring](../wiring/README.md) before
installation. No blower control or remotely operable damper control is included.
Leave all actuator and blower wiring disconnected during monitoring.

## Setup and validation

1. Copy `secrets.example.yaml` to `esphome/secrets.yaml` and replace every
   placeholder with strong, separate credentials. This file is ignored by git;
   never commit or share it. The default broker name `mosquitto` works only if
   the **ESP32's DNS** resolves it; otherwise set `mqtt_broker` to the broker's
   reachable LAN IP or DNS name. Configure broker accounts and permissions
   separately. MQTT here is plaintext; restrict it to a trusted, isolated
   network, or configure and validate TLS for the actual broker and devices.
2. Record each actual DS18B20's unique 64-bit ROM and location and replace
   **every** ROM substitution in the YAMLs. The valid-looking values supplied
   are fictitious examples, not discovery or calibration. ESPHome logs can show
   detected ROMs; identify sensors one at a time, then verify each reading at
   its physical location. Never reuse a ROM for different measurements.
3. Standardize builds on ESPHome **2025.10.3** (the templates reject older
   versions). From the repository root, using the matching container image:

   ```sh
   for node in roof mechanical expansion; do
     docker run --rm -v "$PWD/esphome:/config" \
       ghcr.io/esphome/esphome:2025.10.3 config "/config/$node.yaml"
     docker run --rm -v "$PWD/esphome:/config" \
       ghcr.io/esphome/esphome:2025.10.3 compile "/config/$node.yaml"
   done
   ```

   Alternatively, with ESPHome 2025.10.3 installed locally, check
   `esphome version` and run `esphome config esphome/roof.yaml` and
   `esphome compile esphome/roof.yaml`, substituting each node name. Build
   directories on the host are `esphome/.esphome/build/thermal-roof/`,
   `esphome/.esphome/build/thermal-mechanical/`, and
   `esphome/.esphome/build/thermal-expansion/`. PlatformIO binaries are under
   each build directory's `.pioenvs/<node-name>/`; use the build output to
   identify the appropriate factory/OTA image for the actual board.

   Resolve any board-specific errors. For initial flashing use a suitable USB
   connection and ESPHome's `run` command; subsequent OTA updates require the
   node's OTA password.
   For example, `esphome logs esphome/roof.yaml --device /dev/ttyUSB0` reads
   serial logs when that is the actual device. Ensure updates cannot be made
   by untrusted network clients. Never connect loads just to test firmware.
4. Confirm measurements, source, units, availability and timeouts using the
   [MQTT contract](../mqtt/README.md). Independently compare temperatures
   against a calibrated instrument. Monitor through complete operating cycles
   before considering any controls.

## Sensor wiring

Each node has a separate GPIO4 1-Wire bus:

```text
ESP32 3.3 V ----+-------------------- DS18B20 VDD (all sensors on that bus)
                |
               4.7 kΩ
                |
ESP32 GPIO4 ----+-------------------- DS18B20 DQ
ESP32 GND --------------------------- DS18B20 GND
```

Use externally powered three-wire devices, one pull-up per bus to 3.3 V,
common ground, and a regulated board supply. Do not connect 5 V or 24 VAC to
GPIO. Use a trunk with short stubs, separate from power and motor wiring; test
the actual cable and topology. Verify GPIO4 is available on the selected board;
the example assumes a conventional ESP32 DevKit, not an arbitrary ESP32 model.

| Node | Measurements on GPIO4 |
| --- | --- |
| Roof | Roof inlet, roof outlet, outdoor |
| Mechanical | House supply, house return, mass inlet, mass outlet |
| Expansion | External core |

The external core sensor is a **new, separate** DS18B20 mounted externally;
it does not tap, disconnect, replace, or electrically connect to the legacy
core sensor. Follow the non-destructive survey requirements in safety.md.

## Mechanical outputs and hardware interlocks

GPIO16 and GPIO17 are local-only switches forced OFF on startup and are not
exposed through MQTT; there is no control logic that turns them on. They are
active-high examples, not a relay wiring recommendation. Software initialization
cannot guarantee a GPIO level during reset, loss of power, bootloader operation,
firmware failure, or before initialization. With all loads disconnected, verify
the selected board's pins and use external pull-downs and an appropriately rated,
isolated, **active-high, normally de-energized** driver that remains off across
all power-sequencing and fault states. Avoid active-low relay modules and boot
strapping pins. GPIO16/17 availability varies by board. Test the complete
interface on a bench, including resets, flashing, brownouts and power loss.
No configuration can substitute for independently engineered fail-safe hardware.

Only after qualified site-specific design and commissioning, isolated NO relay
contacts may switch fused 24 VAC through an independent normally-closed safety
chain to spring-return damper actuators. Size supplies, fusing, isolation and
AC-coil suppression for the actual hardware. The independent emergency stop and
watchdog must also remove blower power. Do not connect 24 VAC to the ESP32.
Prove safe airflow with loss of power and do not infer position from commands.
Enabling any control requires a separate reviewed design for feedback,
interlocks, timeouts and non-retained commands; these examples do not provide it.

## Shelly blower plug

Shelly MQTT support, topics, settings, electrical ratings and available telemetry
depend on the exact model and firmware; consult its documentation and configure
it separately. No assumed Shelly topics, commands, firmware flashing, or GPIO
connections are provided here. Have a qualified electrician check motor starting
and continuous current, provide independent hardwired blower safety isolation,
and verify actual airflow. Plug state or power alone is not airflow proof.
