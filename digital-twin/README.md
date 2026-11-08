# Digital twin (observation only)

This standard-library model is an illustrative lumped thermal battery, **not a
safety controller**. It has no hardware, MQTT, sensor wiring, or actuator
interface. Neither estimates nor observation checks authorize operation.
Independent safety interlocks and qualified site commissioning remain essential;
see [safety](../docs/safety.md).

## Physical model

The core is one uniform, effective thermal mass with constant heat capacity
`C = mass_kg * specific_heat_j_kg_k` (J/K). Over each step, inlet and ambient
temperatures, air mass flow, heat input, and properties are constant:

```text
C dT/dt = m_dot * cp_air * (T_in - T) - UA * (T - T_ambient) + Q
```

Temperatures are °C (temperature differences are K), `m_dot` is kg/s, `cp_air`
is J/(kg K), `UA` is W/K, and `Q` is signed thermal power in W delivered
directly to the modeled mass (negative removes heat). The air term assumes
outlet air equilibrates to the core temperature. The analytical solution for
constant inputs is used, including the zero-conductance case; no fixed time
step is required for numerical stability. Model input temperatures must be at
or above absolute zero; a step predicting otherwise is rejected.

Sensible energy relative to a chosen reference is
`E_kWh = C * (T - T_reference) / 3,600,000`; it can be negative or exceed the
usable-window capacity. `SOC_percent = 100 * clamp((T - T_reference) /
(T_maximum - T_reference), 0, 1)` is a **clipped estimate**, not a safety
limit or a measurement. The reference and maximum are explicitly configured
and do not constrain the simulated temperature.

This approximation omits stratification, finite air/core heat-transfer
efficiency, moisture, phase change, temperature-dependent properties,
transport delays and changing conditions within a step. Thermal capacity, loss,
airflow and operating window require measured site-specific calibration. No
example value, default air heat capacity, or simulated result is a rating or
commissioning target. A measured electrical power or relay state is not
automatically thermal input or proof of airflow.

## Protecting the legacy core sensor

Treat the legacy core sensor as irreplaceable. Do not disconnect, energize,
probe, or attach a new circuit to it until its type, existing circuit, voltage
and resistance have been identified non-destructively by qualified personnel.
Use a properly engineered high-impedance buffer or isolation as required, and
document calibration and the interface. The twin never interfaces with the
sensor; `CoreObservation` accepts a number acquired separately. Its explicit
site-defined range and age checks reject stale, future, or implausible samples,
but cannot detect every fault, prove sensor health, or replace independent
protection. Observations do not silently overwrite model state, and a model
estimate must never be substituted for a failed safety sensor.

## Example and tests

Run from the repository root:

```sh
python3 digital-twin/simulate.py
python3 -m unittest discover -s tests -p 'test_twin.py'
```

The simulation runs four one-hour steps each of synthetic charge, hold and
discharge with arbitrary example parameters. It does not read live data.
For another use, import `twin` with `digital-twin` on `PYTHONPATH`, create
`TwinParameters`, `ThermalTwin` and `Conditions`, and call `step` in seconds.
The caller supplies actual timestamp values in epoch seconds to
`CoreObservation.is_usable`; clocks must be synchronized.
