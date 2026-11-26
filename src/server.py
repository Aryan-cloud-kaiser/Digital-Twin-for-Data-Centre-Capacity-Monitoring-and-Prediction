
"""A single virtual server in the simulated data centre."""

from math import isfinite


def _checked_resource(value: float, name: str, *, positive: bool = False) -> float:
    """Validate numeric capacities and demands."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number.")
    if not isfinite(value):
        raise ValueError(f"{name} must be finite.")
    if positive and value <= 0:
        raise ValueError(f"{name} must be greater than zero.")
    if not positive and value < 0:
        raise ValueError(f"{name} cannot be negative.")
    return float(value)


class Server:
    """Represent one server; workload assignment is handled elsewhere."""

    def __init__(
        self,
        server_id: str,
        cpu_capacity: float,
        memory_capacity: float,
        cpu_demand: float = 0,
        memory_demand: float = 0,
        online: bool = True,
    ) -> None:
        if not isinstance(server_id, str) or not server_id.strip():
            raise ValueError("server_id must be a non-empty string.")

        self.server_id = server_id.strip()
        self.cpu_capacity = _checked_resource(
            cpu_capacity, "cpu_capacity", positive=True
        )
        self.memory_capacity = _checked_resource(
            memory_capacity, "memory_capacity", positive=True
        )
        self.cpu_demand = 0.0
        self.memory_demand = 0.0
        self.online = True

        self.update_demand(cpu_demand, memory_demand)
        self.set_online(online)

    def update_demand(self, cpu_demand: float, memory_demand: float) -> None:
        """Set incoming workload. Invalid inputs do not change either value."""
        cpu = _checked_resource(cpu_demand, "cpu_demand")
        memory = _checked_resource(memory_demand, "memory_demand")
        self.cpu_demand = cpu
        self.memory_demand = memory

    def set_online(self, online: bool) -> None:
        """Change availability without deleting the incoming workload."""
        if not isinstance(online, bool):
            raise TypeError("online must be True or False.")
        self.online = online

    @property
    def cpu_served(self) -> float:
        return min(self.cpu_demand, self.cpu_capacity) if self.online else 0.0

    @property
    def memory_served(self) -> float:
        return min(self.memory_demand, self.memory_capacity) if self.online else 0.0

    @property
    def cpu_unmet(self) -> float:
        return self.cpu_demand - self.cpu_served

    @property
    def memory_unmet(self) -> float:
        return self.memory_demand - self.memory_served

    @property
    def cpu_utilisation(self) -> float:
        return (self.cpu_served / self.cpu_capacity) * 100

    @property
    def memory_utilisation(self) -> float:
        return (self.memory_served / self.memory_capacity) * 100

    def snapshot(self) -> dict:
        """Return a plain dictionary for later Twin Core state updates."""
        return {
            "server_id": self.server_id,
            "online": self.online,
            "cpu_capacity": self.cpu_capacity,
            "memory_capacity": self.memory_capacity,
            "cpu_demand": self.cpu_demand,
            "memory_demand": self.memory_demand,
            "cpu_served": self.cpu_served,
            "memory_served": self.memory_served,
            "cpu_unmet": self.cpu_unmet,
            "memory_unmet": self.memory_unmet,
            "cpu_utilisation": self.cpu_utilisation,
            "memory_utilisation": self.memory_utilisation,
        }
