
"""Unit tests for the workload generator."""

import unittest

from src.server import Server
from src.data_centre import DataCentre
from src.workload import WorkloadGenerator


class TestWorkloadGenerator(unittest.TestCase):
    """Test workload scenarios, repeatability and validation."""

    def setUp(self):
        """Create a small data centre for each test."""
        self.server1 = Server("S01", 16, 64)
        self.server2 = Server("S02", 8, 32)

        self.data_centre = DataCentre([
            self.server1,
            self.server2,
        ])

    def test_normal_workload(self):
        """Normal demand should remain within its expected range."""
        generator = WorkloadGenerator("normal", seed=42)
        demands = generator.generate(self.data_centre, 0)

        for server in (self.server1, self.server2):
            demand = demands[server.server_id]

            cpu_ratio = demand["cpu_demand"] / server.cpu_capacity
            memory_ratio = (
                demand["memory_demand"] / server.memory_capacity
            )

            self.assertGreaterEqual(cpu_ratio, 0.52)
            self.assertLessEqual(cpu_ratio, 0.58)
            self.assertGreaterEqual(memory_ratio, 0.42)
            self.assertLessEqual(memory_ratio, 0.48)

    def test_repeatability(self):
        """The same seed and step should produce identical results."""
        generator1 = WorkloadGenerator("normal", seed=42)
        generator2 = WorkloadGenerator("normal", seed=42)

        first = generator1.generate(self.data_centre, 3)
        second = generator2.generate(self.data_centre, 3)

        self.assertEqual(first, second)
        self.assertEqual(
            first,
            generator1.generate(self.data_centre, 3)
        )

    def test_growth_starts_at_normal_level(self):
        """Growth at step zero should match normal workload."""
        normal = WorkloadGenerator("normal", seed=42)
        growth = WorkloadGenerator("growth", seed=42)

        self.assertEqual(
            normal.generate(self.data_centre, 0),
            growth.generate(self.data_centre, 0)
        )

    def test_growth_increases_demand(self):
        """Growth should add the specified demand at each step."""
        normal = WorkloadGenerator("normal", seed=42)
        growth = WorkloadGenerator("growth", seed=42)

        normal_demand = normal.generate(self.data_centre, 4)
        growth_demand = growth.generate(self.data_centre, 4)

        for server in (self.server1, self.server2):
            server_id = server.server_id

            cpu_increase = (
                growth_demand[server_id]["cpu_demand"]
                - normal_demand[server_id]["cpu_demand"]
            )
            memory_increase = (
                growth_demand[server_id]["memory_demand"]
                - normal_demand[server_id]["memory_demand"]
            )

            self.assertAlmostEqual(
                cpu_increase, server.cpu_capacity * 0.20
            )
            self.assertAlmostEqual(
                memory_increase, server.memory_capacity * 0.12
            )

    def test_spike_at_step_five(self):
        """The spike scenario should increase demand at step five."""
        normal = WorkloadGenerator("normal", seed=42)
        spike = WorkloadGenerator("spike", seed=42)

        normal_demand = normal.generate(self.data_centre, 5)
        spike_demand = spike.generate(self.data_centre, 5)

        for server in (self.server1, self.server2):
            server_id = server.server_id

            self.assertAlmostEqual(
                spike_demand[server_id]["cpu_demand"],
                normal_demand[server_id]["cpu_demand"] * 2
            )
            self.assertAlmostEqual(
                spike_demand[server_id]["memory_demand"],
                normal_demand[server_id]["memory_demand"] * 1.8
            )

    def test_spike_only_at_step_five(self):
        """Other steps should behave like normal workload."""
        normal = WorkloadGenerator("normal", seed=42)
        spike = WorkloadGenerator("spike", seed=42)

        for step in (4, 6):
            self.assertEqual(
                normal.generate(self.data_centre, step),
                spike.generate(self.data_centre, step)
            )

    def test_generation_does_not_change_servers(self):
        """Generating workloads must not modify server state."""
        self.server1.update_demand(6, 20)
        before = self.data_centre.snapshot()

        generator = WorkloadGenerator("growth", seed=42)
        generator.generate(self.data_centre, 4)

        after = self.data_centre.snapshot()

        self.assertEqual(before, after)

    def test_empty_data_centre(self):
        """An empty data centre should produce no workloads."""
        generator = WorkloadGenerator("normal")
        empty = DataCentre()

        self.assertEqual(generator.generate(empty, 0), {})

    def test_invalid_configuration(self):
        """Invalid scenarios and seeds should be rejected."""
        with self.assertRaises(ValueError):
            WorkloadGenerator("unknown")

        with self.assertRaises(TypeError):
            WorkloadGenerator("normal", seed=1.5)

        with self.assertRaises(TypeError):
            WorkloadGenerator("normal", seed=True)

    def test_invalid_generation_inputs(self):
        """Invalid steps and data-centre objects must be rejected."""
        generator = WorkloadGenerator("normal")

        with self.assertRaises(ValueError):
            generator.generate(self.data_centre, -1)

        with self.assertRaises(ValueError):
            generator.generate(self.data_centre, 1.5)

        with self.assertRaises(ValueError):
            generator.generate(self.data_centre, True)

        with self.assertRaises(TypeError):
            generator.generate("not a data centre", 0)


if __name__ == "__main__":
    unittest.main()
