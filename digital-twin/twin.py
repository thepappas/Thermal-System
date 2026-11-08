"""Observation-only, lumped thermal battery model using SI units."""

from dataclasses import dataclass
import math


ABSOLUTE_ZERO_C = -273.15
JOULES_PER_KWH = 3_600_000.0


def _number(name, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    try:
        value = float(value)
    except OverflowError as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return value


def _temperature(name, value):
    value = _number(name, value)
    if value < ABSOLUTE_ZERO_C:
        raise ValueError(f"{name} must be at or above absolute zero")
    return value


@dataclass(frozen=True)
class TwinParameters:
    """Effective material properties and the usable temperature window."""

    mass_kg: float
    specific_heat_j_kg_k: float
    loss_w_per_k: float
    reference_temp_c: float
    maximum_temp_c: float
    air_specific_heat_j_kg_k: float = 1005.0

    def __post_init__(self):
        mass = _number("mass_kg", self.mass_kg)
        heat = _number("specific_heat_j_kg_k", self.specific_heat_j_kg_k)
        air_heat = _number("air_specific_heat_j_kg_k", self.air_specific_heat_j_kg_k)
        loss = _number("loss_w_per_k", self.loss_w_per_k)
        reference = _temperature("reference_temp_c", self.reference_temp_c)
        maximum = _temperature("maximum_temp_c", self.maximum_temp_c)
        if mass <= 0 or heat <= 0 or air_heat <= 0 or loss < 0:
            raise ValueError("mass and specific heats must be positive; loss must be nonnegative")
        if maximum <= reference:
            raise ValueError("maximum_temp_c must exceed reference_temp_c")
        if not math.isfinite(mass * heat) or mass * heat <= 0:
            raise ValueError("thermal capacity must be positive and finite")

    @property
    def capacity_j_per_k(self):
        return self.mass_kg * self.specific_heat_j_kg_k


@dataclass(frozen=True)
class Conditions:
    """Conditions held constant over a model step; heat input may be signed."""

    inlet_temp_c: float
    ambient_temp_c: float
    air_mass_flow_kg_s: float
    heat_input_w: float = 0.0

    def __post_init__(self):
        _temperature("inlet_temp_c", self.inlet_temp_c)
        _temperature("ambient_temp_c", self.ambient_temp_c)
        if _number("air_mass_flow_kg_s", self.air_mass_flow_kg_s) < 0:
            raise ValueError("air_mass_flow_kg_s must be nonnegative")
        _number("heat_input_w", self.heat_input_w)


class ThermalTwin:
    """A single perfectly mixed thermal mass; never reads or controls hardware."""

    def __init__(self, parameters, initial_temp_c):
        if not isinstance(parameters, TwinParameters):
            raise ValueError("parameters must be TwinParameters")
        self.parameters = parameters
        self._temperature_c = _temperature("initial_temp_c", initial_temp_c)

    @property
    def temperature_c(self):
        return self._temperature_c

    @property
    def energy_kwh(self):
        """Signed sensible energy relative to the configured reference."""
        p = self.parameters
        return p.capacity_j_per_k * (self.temperature_c - p.reference_temp_c) / JOULES_PER_KWH

    @property
    def soc_percent(self):
        """Temperature-based usable SOC, clipped to 0–100 percent."""
        p = self.parameters
        fraction = (self.temperature_c - p.reference_temp_c) / (p.maximum_temp_c - p.reference_temp_c)
        return 100.0 * min(1.0, max(0.0, fraction))

    def step(self, conditions, duration_s):
        """Advance with constant boundary conditions and return the new temperature."""
        if not isinstance(conditions, Conditions):
            raise ValueError("conditions must be Conditions")
        duration = _number("duration_s", duration_s)
        if duration <= 0:
            raise ValueError("duration_s must be positive")
        p = self.parameters
        flow_conductance = conditions.air_mass_flow_kg_s * p.air_specific_heat_j_kg_k
        conductance = flow_conductance + p.loss_w_per_k
        net_power = (flow_conductance * (conditions.inlet_temp_c - self.temperature_c)
                     - p.loss_w_per_k * (self.temperature_c - conditions.ambient_temp_c)
                     + conditions.heat_input_w)
        if not math.isfinite(conductance) or not math.isfinite(net_power):
            raise ValueError("conditions produce non-finite heat flow")
        # Exact solution of C*dT/dt = net_power - conductance*(T - T_initial).
        if conductance == 0:
            delta = net_power * (duration / p.capacity_j_per_k)
        else:
            decay = -math.expm1(-conductance * duration / p.capacity_j_per_k)
            delta = (net_power / conductance) * decay
        new_temp = _temperature("resulting temperature", self.temperature_c + delta)
        self._temperature_c = new_temp
        return new_temp


@dataclass(frozen=True)
class CoreObservation:
    """A separately acquired, read-only core observation, with epoch seconds."""

    temperature_c: float
    observed_at_s: float

    def __post_init__(self):
        _temperature("temperature_c", self.temperature_c)
        _number("observed_at_s", self.observed_at_s)

    def is_usable(self, now_s, max_age_s, minimum_c, maximum_c):
        """Check configured plausibility and freshness; this does not certify safety."""
        now = _number("now_s", now_s)
        age_limit = _number("max_age_s", max_age_s)
        minimum = _temperature("minimum_c", minimum_c)
        maximum = _temperature("maximum_c", maximum_c)
        if age_limit < 0 or maximum < minimum:
            raise ValueError("invalid age limit or temperature range")
        age = now - self.observed_at_s
        return 0 <= age <= age_limit and minimum <= self.temperature_c <= maximum
