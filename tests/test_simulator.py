
"""Unit tests for the simulation controller."""

import unittest

from src.server import Server
from src.data_centre import DataCentre
from src.workload import WorkloadGenerator
from src.simulator import Simulator


class TestSimulator(unittest.TestCase):
    """Verify simulation steps, state updates and history."""

    def setUp(self):
        """Create a fresh simulation before every test."""
        self.data_centre = DataCentre([
            Server("S01", 16, 64),
            Server("S02", 8, 32),
        ])

        self.generator = WorkloadGenerator("normal", seed=42)

        self.simulator = Simulator(
            self.data_centre,
            self.generator,
        )

    def test_initial_state(self):
        """A new simulation should start at step zero."""
        self.assertEqual(self.simulator.current_step, 0)
        self.assertEqual(self.simulator.history, [])

    def test_invalid_constructor(self):
        """The simulator requires valid component objects."""
        with self.assertRaises(TypeError):
            Simulator("invalid", self.generator)

        with self.assertRaises(TypeError):
            Simulator(self.data_centre, "invalid")

    def test_single_step(self):
        """Executing one step should advance the simulation."""
        result = self.simulator.step()

        self.assertEqual(result["step"], 0)
        self.assertEqual(result["scenario"], "normal")
        self.assertEqual(result["seed"], 42)

        self.assertEqual(self.simulator.current_step, 1)
        self.assertEqual(len(self.simulator.history), 1)

    def test_workloads_are_applied(self):
        """Generated demands should update the correct servers."""
        expected = self.generator.generate(
            self.data_centre, 0
        )

        result = self.simulator.step()

        for server_id, demand in expected.items():
            server = self.data_centre.get_server(server_id)

            self.assertAlmostEqual(
                server.cpu_demand, demand["cpu_demand"]
            )
            self.assertAlmostEqual(
                server.memory_demand, demand["memory_demand"]
            )

        self.assertEqual(
            result["state"], self.data_centre.snapshot()
        )

    def test_run_multiple_steps(self):
        """Run should execute and record the requested steps."""
        results = self.simulator.run(3)

        self.assertEqual(len(results), 3)
        self.assertEqual(
            [record["step"] for record in results],
            [0, 1, 2],
        )
        self.assertEqual(self.simulator.current_step, 3)
        self.assertEqual(len(self.simulator.history), 3)

    def test_run_continues_simulation(self):
        """Calling run again should continue from the last step."""
        self.simulator.run(2)
        results = self.simulator.run(2)

        self.assertEqual(
            [record["step"] for record in results],
            [2, 3],
        )
        self.assertEqual(self.simulator.current_step, 4)
        self.assertEqual(len(self.simulator.history), 4)

    def test_zero_steps(self):
        """Running zero steps should leave the simulation unchanged."""
        result = self.simulator.run(0)

        self.assertEqual(result, [])
        self.assertEqual(self.simulator.current_step, 0)
        self.assertEqual(self.simulator.history, [])

    def test_invalid_run_inputs(self):
        """Invalid step counts must be rejected."""
        for invalid in (1.5, "3", True, None):
            with self.subTest(value=invalid):
                with self.assertRaises(TypeError):
                    self.simulator.run(invalid)

        with self.assertRaises(ValueError):
            self.simulator.run(-1)

        self.assertEqual(self.simulator.current_step, 0)
        self.assertEqual(self.simulator.history, [])

    def test_history_preserves_previous_states(self):
        """Later steps should not change earlier records."""
        first = self.simulator.step()
        self.simulator.step()

        history = self.simulator.history

        self.assertEqual(len(history), 2)
        self.assertEqual(history[0], first)
        self.assertEqual(history[0]["step"], 0)
        self.assertEqual(history[1]["step"], 1)

    def test_history_is_protected(self):
        """Changing returned data must not alter saved history."""
        result = self.simulator.step()

        result["state"]["servers"][0]["cpu_demand"] = -999

        self.assertNotEqual(
            self.simulator.history[0]["state"]["servers"][0]["cpu_demand"],
            -999,
        )

        history_copy = self.simulator.history
        history_copy[0]["state"]["server_count"] = 999

        self.assertEqual(
            self.simulator.history[0]["state"]["server_count"],
            2,
        )

    def test_repeatable_simulation(self):
        """Equal seeds and initial states should give equal results."""
        first_results = self.simulator.run(6)

        second_centre = DataCentre([
            Server("S01", 16, 64),
            Server("S02", 8, 32),
        ])

        second_simulator = Simulator(
            second_centre,
            WorkloadGenerator("normal", seed=42),
        )

        second_results = second_simulator.run(6)

        self.assertEqual(first_results, second_results)

    def test_offline_server(self):
        """An offline server should not contribute available capacity."""
        server2 = self.data_centre.get_server("S02")
        server2.set_online(False)

        result = self.simulator.step()
        state = result["state"]

        self.assertEqual(state["online_count"], 1)
        self.assertEqual(state["cpu_capacity_online"], 16)
        self.assertEqual(state["memory_capacity_online"], 64)

        self.assertEqual(server2.cpu_served, 0)
        self.assertEqual(server2.memory_served, 0)

        self.assertAlmostEqual(
            server2.cpu_unmet, server2.cpu_demand
        )

    def test_spike_at_step_five(self):
        """The spike scenario should increase demand at step five."""
        spike_simulator = Simulator(
            self.data_centre,
            WorkloadGenerator("spike", seed=42),
        )

        results = spike_simulator.run(6)
        spike_state = results[5]["state"]

        normal = WorkloadGenerator("normal", seed=42)
        expected = normal.generate(self.data_centre, 5)

        for server_state in spike_state["servers"]:
            server_id = server_state["server_id"]

            self.assertAlmostEqual(
                server_state["cpu_demand"],
                expected[server_id]["cpu_demand"] * 2,
            )
            self.assertAlmostEqual(
                server_state["memory_demand"],
                expected[server_id]["memory_demand"] * 1.8,
            )

        self.assertGreater(spike_state["cpu_unmet"], 0)


if __name__ == "__main__":
    unittest.main()
