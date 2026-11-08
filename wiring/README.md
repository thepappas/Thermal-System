# Wiring and field survey

**Disconnect and verify absence of power before work.** Mains and 24 VAC
wiring must be installed and inspected by qualified personnel. Follow device
datasheets and local codes; these conceptual diagrams are not construction
drawings.

## ESP32 and DS18B20

```text
regulated 3.3 V ----+------------ DS18B20 VDD
                    |
                   4.7k
                    |
ESP32 GPIO ---------+------------ DS18B20 DQ
ESP32 GND ----------------------- DS18B20 GND
```

Use externally powered three-wire sensors, a 4.7 kΩ pull-up to 3.3 V, common
ground, and a regulated supply appropriate to the ESP32 board. Prefer twisted
pair cable, a linear trunk and short stubs. Pair data with ground; segregate
from mains, motor and relay wiring. Shield termination and surge protection
depend on the installation. There is no universal safe maximum length: cable
capacitance, topology, pull-up and electrical noise determine reliability.
Bench-test the actual cable, start short and validate at temperature extremes.
Document each unique 64-bit sensor ROM and location.

## Damper isolation

```text
24 VAC transformer R -- fuse -- NC safety chain -- relay NO -- actuator lead
24 VAC transformer C ---------------------------------------- actuator lead
ESP32 GPIO -- isolated, correctly rated relay driver -- relay coil
```

Confirm wiring against the actual Honeywell datasheet. The safety chain and
watchdog must independently remove 24 VAC. Size transformer and fuse for all
simultaneous actuator loads; do not connect 24 VAC to ESP32 GPIO. Suppression
must be appropriate for AC coils and the relay contacts. Test spring return
with power removed and verify the resulting airflow is safe.

## Blower

Connect the blower only to a Shelly plug rated for its motor starting and
continuous current. Confirm local MQTT support and configuration for the
specific model. Integrate an independent hardwired safety disconnect; plug
relay state and current/power telemetry are not proof of airflow. Never expose
the plug's mains terminals while energized.
