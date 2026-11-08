# Node-RED monitoring flow

Import `flows.json` or mount it as the runtime flow file. The flow subscribes
to `hvac/#`, writes the numeric observations listed in the function to the
InfluxDB `hvac` measurement, and publishes `hvac/controller/mode`.
The controller is **advisory only**: it never commands a damper or blower.
Defaults to `IDLE`; stale or invalid inputs result in `FAILSAFE`. `AUTO` and
`DIAGNOSTICS` can be exercised in simulation by setting flow context
`requested` to that value. Restart resets the request to idle.

The provisional priority order is charge (roof − core ≥ 5 °C), heat
(mass outlet − house return ≥ 3 °C), cooling (house return − roof ≥ 4 °C),
then idle. These thresholds do not provide night detection, seasonal policy,
hysteresis, minimum runtime, position feedback or airflow proof. Therefore
the recommendations must not be used to energize equipment. Diagnostics is
also advisory and never bypasses stale sensor checks. `FAILSAFE` describes
the recommendation, not physical proof that outputs are de-energized.

Inputs must be non-retained live numeric readings, −50 to 100 °C; all four
must arrive within 120 seconds. Values are timestamped on receipt, so network
delay is not measured. Configure publishing intervals accordingly. Loss of
Node-RED means there is no state publication: downstream must independently
time out, and hardware must fail safe.

The InfluxDB writer drops retained and malformed messages; it has no offline
queue. Failures are logged in Node-RED and data during outages is lost.
Configure alerting and backups appropriate to the installation. Credentials
and ports are deployment-specific; never expose the editor to untrusted
networks.
