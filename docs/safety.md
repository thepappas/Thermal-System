# Safety and commissioning boundary

This software is not a safety-rated controller. A server crash, WiFi outage,
broker failure, stuck relay, welded contact, or loss of ESP32 power must not
cause an unsafe condition. Have a qualified HVAC controls professional and
electrician evaluate the installation, local codes, transformer capacity,
grounding, duct pressure, fire/smoke protection, freeze protection, and
motor limits. Preserve any independent legacy safety controls.

Honeywell M836B1033 actuators are assumed to open with 24 VAC and spring closed
without power. Verify the actual actuator, end switches, terminal markings and
manufacturer data before wiring. Do not infer position from a command.

Independent hardware must remove actuator **and blower power** on emergency
stop or controller watchdog failure. A WiFi-controlled plug alone cannot
guarantee that the blower stops when communication is lost. Design a safe
airflow path and prove it with measured airflow/pressure. Relays must be
normally open, isolated, rated for the load and fail de-energized. Ensure
ESP32 boot pins, relay board polarity and power sequencing cannot energize
outputs unexpectedly. Provide a local means to isolate all power.

Automatic operation requires site-specific validation of fresh, plausible
measurements, valid routes, blower and damper feedback, output timeouts,
hysteresis, minimum cycle times, fault latching and manual reset. No remote
command should bypass these protections. Never use retained MQTT commands.

Treat the legacy core sensor as irreplaceable: do not disconnect or energize
its wiring until its type, existing circuit, voltage and resistance are
identified non-destructively. Buffer or isolate measurements as required;
document calibration and replacement interfaces.
