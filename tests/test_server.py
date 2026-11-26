
"""Unit tests for the virtual Server model."""

import unittest

from src.server import Server


class TestServer(unittest.TestCase):
    """Check the behaviour of a single virtual server."""

    def setUp(self):
        """Create a fresh server before every test."""
        self.server = Server("S01", 16, 64)

    def test_initialisation(self):
        """A new server should start online with no workload."""
        self.assertEqual(self.server.server_id, "S01")
        self.assertEqual(self.server.cpu_capacity, 16)
        self.assertEqual(self.server.memory_capacity, 64)
        self.assertTrue(self.server.online)
        self.assertEqual(self.server.cpu_demand, 0)
        self.assertEqual(self.server.memory_demand, 0)

    def test_normal_workload(self):
        """Demand within capacity should be fully served."""
        self.server.update_demand(8, 24)

        self.assertEqual(self.server.cpu_served, 8)
        self.assertEqual(self.server.memory_served, 24)
        self.assertEqual(self.server.cpu_unmet, 0)
        self.assertEqual(self.server.memory_unmet, 0)
        self.assertAlmostEqual(self.server.cpu_utilisation, 50)
        self.assertAlmostEqual(self.server.memory_utilisation, 37.5)

    def test_overload(self):
        """Demand above capacity should create unmet demand."""
        self.server.update_demand(20, 80)

        self.assertEqual(self.server.cpu_served, 16)
        self.assertEqual(self.server.memory_served, 64)
        self.assertEqual(self.server.cpu_unmet, 4)
        self.assertEqual(self.server.memory_unmet, 16)
        self.assertEqual(self.server.cpu_utilisation, 100)
        self.assertEqual(self.server.memory_utilisation, 100)

    def test_offline_and_recovery(self):
        """An offline server cannot serve incoming demand."""
        self.server.update_demand(8, 24)
        self.server.set_online(False)

        self.assertFalse(self.server.online)
        self.assertEqual(self.server.cpu_served, 0)
        self.assertEqual(self.server.memory_served, 0)
        self.assertEqual(self.server.cpu_unmet, 8)
        self.assertEqual(self.server.memory_unmet, 24)

        self.server.set_online(True)

        self.assertTrue(self.server.online)
        self.assertEqual(self.server.cpu_served, 8)
        self.assertEqual(self.server.memory_served, 24)

    def test_invalid_capacity(self):
        """Server capacities must be positive."""
        with self.assertRaises(ValueError):
            Server("S02", 0, 64)

        with self.assertRaises(ValueError):
            Server("S03", 16, -10)

    def test_invalid_workload(self):
        """Invalid demand must not change existing values."""
        self.server.update_demand(4, 12)

        with self.assertRaises(ValueError):
            self.server.update_demand(10, -5)

        self.assertEqual(self.server.cpu_demand, 4)
        self.assertEqual(self.server.memory_demand, 12)

        with self.assertRaises(ValueError):
            self.server.update_demand(float("nan"), 10)

    def test_invalid_availability(self):
        """Server availability must be a boolean."""
        with self.assertRaises(TypeError):
            self.server.set_online("offline")

    def test_snapshot(self):
        """A snapshot should contain the current server state."""
        self.server.update_demand(8, 24)
        state = self.server.snapshot()

        self.assertEqual(state["server_id"], "S01")
        self.assertTrue(state["online"])
        self.assertEqual(state["cpu_demand"], 8)
        self.assertEqual(state["memory_demand"], 24)
        self.assertEqual(state["cpu_utilisation"], 50)
        self.assertEqual(state["memory_utilisation"], 37.5)


if __name__ == "__main__":
    unittest.main()
