
"""Generate repeatable CPU and memory demand for simulated servers."""

import random

from src.data_centre import DataCentre


class WorkloadGenerator:
    """Generate normal, growing, or short-spike workloads."""

    def __init__(self, scenario: str = "normal", seed: int = 42) -> None:
        if scenario not in ("normal", "growth", "spike"):
            raise ValueError("scenario must be normal, growth or spike.")
        if type(seed) is not int:
            raise TypeError("seed must be an integer.")

        self.scenario = scenario
        self.seed = seed

    def generate(self, data_centre: DataCentre, step: int) -> dict[str, dict[str, float]]:
        """Return per-server demand without modifying any server state."""
        if not isinstance(data_centre, DataCentre):
            raise TypeError("data_centre must be a DataCentre instance.")
        if type(step) is not int or step < 0:
            raise ValueError("step must be a non-negative integer.")

        demands = {}

        for server in data_centre.snapshot()["servers"]:
            rng = random.Random(f"{self.seed}:{step}:{server['server_id']}")

            cpu_ratio = 0.55 + rng.uniform(-0.03, 0.03)
            memory_ratio = 0.45 + rng.uniform(-0.03, 0.03)

            if self.scenario == "growth":
                cpu_ratio += 0.05 * step
                memory_ratio += 0.03 * step

            elif self.scenario == "spike" and step == 5:
                cpu_ratio *= 2.0
                memory_ratio *= 1.8

            demands[server["server_id"]] = {
                "cpu_demand": server["cpu_capacity"] * cpu_ratio,
                "memory_demand": server["memory_capacity"] * memory_ratio,
            }

        return demands
