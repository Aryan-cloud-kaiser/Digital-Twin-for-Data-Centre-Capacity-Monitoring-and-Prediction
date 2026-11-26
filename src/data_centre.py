
"""Manage multiple virtual servers in a simulated data centre."""

from src.server import Server


class DataCentre:
    """A collection of virtual servers and their resource totals."""

    def __init__(self, servers: list[Server] | None = None) -> None:
        self._servers: dict[str, Server] = {}

        if servers is not None:
            for server in servers:
                self.add_server(server)

    def add_server(self, server: Server) -> None:
        """Add a server, ensuring its ID is unique."""
        if not isinstance(server, Server):
            raise TypeError("server must be a Server instance.")

        if server.server_id in self._servers:
            raise ValueError(f"Duplicate server ID: {server.server_id}")

        self._servers[server.server_id] = server

    def get_server(self, server_id: str) -> Server:
        """Retrieve a server by its ID."""
        if server_id not in self._servers:
            raise KeyError(f"Unknown server ID: {server_id}")

        return self._servers[server_id]

    def snapshot(self) -> dict:
        """Return the current server states and combined resource totals."""
        servers = list(self._servers.values())
        active = [server for server in servers if server.online]

        cpu_capacity = sum(s.cpu_capacity for s in active)
        memory_capacity = sum(s.memory_capacity for s in active)

        cpu_served = sum(s.cpu_served for s in servers)
        memory_served = sum(s.memory_served for s in servers)

        return {
            "server_count": len(servers),
            "online_count": len(active),
            "cpu_capacity_online": cpu_capacity,
            "memory_capacity_online": memory_capacity,
            "cpu_demand": sum(s.cpu_demand for s in servers),
            "memory_demand": sum(s.memory_demand for s in servers),
            "cpu_served": cpu_served,
            "memory_served": memory_served,
            "cpu_unmet": sum(s.cpu_unmet for s in servers),
            "memory_unmet": sum(s.memory_unmet for s in servers),
            "cpu_utilisation": (
                cpu_served / cpu_capacity * 100
                if cpu_capacity else 0.0
            ),
            "memory_utilisation": (
                memory_served / memory_capacity * 100
                if memory_capacity else 0.0
            ),
            "servers_with_unmet_demand": [
                s.server_id for s in servers
                if s.cpu_unmet > 0 or s.memory_unmet > 0
            ],
            "servers": [s.snapshot() for s in servers],
        }
