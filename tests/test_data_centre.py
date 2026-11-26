
"""Unit tests for the DataCentre model."""

import unittest

from src.server import Server
from src.data_centre import DataCentre


class TestDataCentre(unittest.TestCase):
    """Check server management and data-centre resource totals."""

    def setUp(self):
        """Create two servers and an empty data centre."""
        self.server1 = Server("S01", 16, 64)
        self.server2 = Server("S02", 16, 64)
        self.data_centre = DataCentre()

    def test_add_server(self):
        """A valid server should be added successfully."""
        self.data_centre.add_server(self.server1)

        self.assertEqual(
            self.data_centre.snapshot()["server_count"], 1
        )

    def test_get_server(self):
        """An existing server should be retrievable by ID."""
        self.data_centre.add_server(self.server1)

        result = self.data_centre.get_server("S01")

        self.assertIs(result, self.server1)

    def test_initialise_with_servers(self):
        """A data centre can be created with existing servers."""
        data_centre = DataCentre([self.server1, self.server2])

        self.assertEqual(
            data_centre.snapshot()["server_count"], 2
        )

    def test_duplicate_server(self):
        """Duplicate server IDs should be rejected."""
        self.data_centre.add_server(self.server1)

        with self.assertRaises(ValueError):
            self.data_centre.add_server(
                Server("S01", 8, 32)
            )

    def test_invalid_server(self):
        """Only Server objects should be accepted."""
        with self.assertRaises(TypeError):
            self.data_centre.add_server("S03")

    def test_unknown_server(self):
        """Requesting a missing server should raise an error."""
        with self.assertRaises(KeyError):
            self.data_centre.get_server("S99")

    def test_empty_data_centre(self):
        """An empty data centre should have zero resources."""
        state = self.data_centre.snapshot()

        self.assertEqual(state["server_count"], 0)
        self.assertEqual(state["online_count"], 0)
        self.assertEqual(state["cpu_capacity_online"], 0)
        self.assertEqual(state["memory_capacity_online"], 0)
        self.assertEqual(state["cpu_utilisation"], 0)
        self.assertEqual(state["memory_utilisation"], 0)

    def test_resource_totals(self):
        """The data centre should combine server resources."""
        self.server1.update_demand(8, 24)
        self.server2.update_demand(12, 32)

        self.data_centre.add_server(self.server1)
        self.data_centre.add_server(self.server2)

        state = self.data_centre.snapshot()

        self.assertEqual(state["server_count"], 2)
        self.assertEqual(state["online_count"], 2)
        self.assertEqual(state["cpu_capacity_online"], 32)
        self.assertEqual(state["memory_capacity_online"], 128)
        self.assertEqual(state["cpu_demand"], 20)
        self.assertEqual(state["memory_demand"], 56)
        self.assertEqual(state["cpu_served"], 20)
        self.assertEqual(state["memory_served"], 56)
        self.assertAlmostEqual(state["cpu_utilisation"], 62.5)
        self.assertAlmostEqual(state["memory_utilisation"], 43.75)

    def test_server_failure(self):
        """An offline server should not provide usable capacity."""
        self.server1.update_demand(8, 24)
        self.server2.update_demand(12, 32)
        self.server2.set_online(False)

        self.data_centre.add_server(self.server1)
        self.data_centre.add_server(self.server2)

        state = self.data_centre.snapshot()

        self.assertEqual(state["online_count"], 1)
        self.assertEqual(state["cpu_capacity_online"], 16)
        self.assertEqual(state["memory_capacity_online"], 64)
        self.assertEqual(state["cpu_served"], 8)
        self.assertEqual(state["memory_served"], 24)
        self.assertEqual(state["cpu_unmet"], 12)
        self.assertEqual(state["memory_unmet"], 32)

    def test_overloaded_server(self):
        """Unmet demand must remain visible at server level."""
        self.server1.update_demand(20, 80)
        self.server2.update_demand(4, 16)

        self.data_centre.add_server(self.server1)
        self.data_centre.add_server(self.server2)

        state = self.data_centre.snapshot()

        self.assertEqual(state["cpu_unmet"], 4)
        self.assertEqual(state["memory_unmet"], 16)
        self.assertEqual(
            state["servers_with_unmet_demand"], ["S01"]
        )
        self.assertAlmostEqual(state["cpu_utilisation"], 62.5)

    def test_snapshot_updates(self):
        """Snapshots should reflect subsequent workload changes."""
        self.data_centre.add_server(self.server1)

        before = self.data_centre.snapshot()

        self.server1.update_demand(8, 24)

        after = self.data_centre.snapshot()

        self.assertEqual(before["cpu_demand"], 0)
        self.assertEqual(after["cpu_demand"], 8)
        self.assertEqual(after["memory_demand"], 24)


if __name__ == "__main__":
    unittest.main()
