"""Run a synthetic, illustrative charge/hold/discharge simulation."""

from twin import Conditions, ThermalTwin, TwinParameters


def main():
    parameters = TwinParameters(
        mass_kg=10_000, specific_heat_j_kg_k=800, loss_w_per_k=15,
        reference_temp_c=20, maximum_temp_c=60,
    )
    twin = ThermalTwin(parameters, initial_temp_c=25)
    phases = (
        ("charge", Conditions(inlet_temp_c=80, ambient_temp_c=20, air_mass_flow_kg_s=0.25)),
        ("hold", Conditions(inlet_temp_c=20, ambient_temp_c=20, air_mass_flow_kg_s=0)),
        ("discharge", Conditions(inlet_temp_c=15, ambient_temp_c=20, air_mass_flow_kg_s=0.25)),
    )
    print("phase       hours    core °C    energy kWh    SOC %")
    for phase, conditions in phases:
        for hour in range(1, 5):
            twin.step(conditions, 3600)
            print(f"{phase:10} {hour:5} {twin.temperature_c:10.2f}"
                  f" {twin.energy_kwh:13.2f} {twin.soc_percent:8.1f}")


if __name__ == "__main__":
    main()
