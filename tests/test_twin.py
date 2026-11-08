import math
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "digital-twin"))

from twin import Conditions, CoreObservation, ThermalTwin, TwinParameters


class TwinTests(unittest.TestCase):
    def setUp(self):
        self.params = TwinParameters(1000, 1000, 10, 20, 60, 1000)

    def test_energy_and_clipped_soc(self):
        twin = ThermalTwin(self.params, 40)
        self.assertAlmostEqual(twin.energy_kwh, 20_000_000 / 3_600_000)
        self.assertEqual(twin.soc_percent, 50)
        self.assertLess(ThermalTwin(self.params, 10).energy_kwh, 0)
        self.assertEqual(ThermalTwin(self.params, 10).soc_percent, 0)
        self.assertEqual(ThermalTwin(self.params, 80).soc_percent, 100)

    def test_exact_solution_and_step_partition(self):
        conditions = Conditions(80, 20, 0.1, 500)
        one = ThermalTwin(self.params, 30)
        many = ThermalTwin(self.params, 30)
        one.step(conditions, 3600)
        for _ in range(60):
            many.step(conditions, 60)
        equilibrium = (100 * 80 + 10 * 20 + 500) / 110
        expected = equilibrium + (30 - equilibrium) * math.exp(-110 * 3600 / 1_000_000)
        self.assertAlmostEqual(one.temperature_c, expected)
        self.assertAlmostEqual(one.temperature_c, many.temperature_c)

    def test_zero_conductance_and_cooling(self):
        params = TwinParameters(1000, 1000, 0, 20, 60)
        twin = ThermalTwin(params, 30)
        twin.step(Conditions(20, 20, 0, 1000), 1000)
        self.assertAlmostEqual(twin.temperature_c, 31)
        twin.step(Conditions(20, 20, 0, -1000), 1000)
        self.assertAlmostEqual(twin.temperature_c, 30)
        twin.step(Conditions(10, 20, 0.2), 3600)
        self.assertLess(twin.temperature_c, 30)

    def test_ambient_loss_and_equilibrium(self):
        twin = ThermalTwin(self.params, 50)
        twin.step(Conditions(20, 20, 0), 3600)
        self.assertAlmostEqual(twin.temperature_c, 20 + 30 * math.exp(-0.036))
        equilibrium = ThermalTwin(self.params, 20)
        equilibrium.step(Conditions(20, 20, 0), 3600)
        self.assertEqual(equilibrium.temperature_c, 20)

    def test_invalid_inputs_and_atomic_step(self):
        for args in [(0, 1000, 10, 20, 60), (1000, 0, 10, 20, 60),
                     (1000, 1000, -1, 20, 60), (1000, 1000, 10, 60, 60),
                     (math.inf, 1000, 10, 20, 60), (True, 1000, 10, 20, 60),
                     (1e-300, 1e-300, 10, 20, 60),
                     (1000, 1000, 10, -274, 60)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                TwinParameters(*args)
        for args in [(20, 20, -1), (math.nan, 20, 0), (20, 20, 0, math.inf)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                Conditions(*args)
        twin = ThermalTwin(TwinParameters(1, 1, 0, 0, 10), 0)
        for duration in (0, -1, math.nan):
            with self.assertRaises(ValueError):
                twin.step(Conditions(20, 20, 0), duration)
        with self.assertRaises(ValueError):
            twin.step(Conditions(20, 20, 0, -1000), 1)
        self.assertEqual(twin.temperature_c, 0)

    def test_core_observation_validation(self):
        observation = CoreObservation(40, 100)
        self.assertTrue(observation.is_usable(110, 10, 20, 60))
        self.assertFalse(observation.is_usable(111, 10, 20, 60))
        self.assertFalse(observation.is_usable(99, 10, 20, 60))
        self.assertFalse(observation.is_usable(100, 10, 41, 60))
        with self.assertRaises(ValueError):
            observation.is_usable(100, -1, 20, 60)
        with self.assertRaises(ValueError):
            observation.is_usable(100, 10, 60, 20)
        with self.assertRaises(ValueError):
            CoreObservation(math.nan, 100)

    def test_synthetic_simulation_runs(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "digital-twin" / "simulate.py")],
            check=True, capture_output=True, text=True,
        )
        self.assertEqual(len(result.stdout.splitlines()), 13)
        for phase in ("charge", "hold", "discharge"):
            self.assertIn(phase, result.stdout)


if __name__ == "__main__":
    unittest.main()
