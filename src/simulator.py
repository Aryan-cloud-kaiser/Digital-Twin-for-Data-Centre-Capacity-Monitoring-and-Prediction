
"""Control simulation steps and record data-centre states."""

from copy import deepcopy

from src.data_centre import DataCentre
from src.workload import WorkloadGenerator


class Simulator:
    """Run a simulated data centre using generated workloads."""

    def __init__(
        self,
        data_centre: DataCentre,
        workload_generator: WorkloadGenerator,
    ) -> None:
        if not isinstance(data_centre, DataCentre):
            raise TypeError("data_centre must be a DataCentre instance.")

        if not isinstance(workload_generator, WorkloadGenerator):
            raise TypeError(
                "workload_generator must be a WorkloadGenerator instance."
            )

        self.data_centre = data_centre
        self.workload_generator = workload_generator
        self.current_step = 0
        self._history = []

    def step(self) -> dict:
        """Advance the simulation by one step."""

        demands = self.workload_generator.generate(
            self.data_centre,
            self.current_step,
        )

        for server_id, demand in demands.items():
            server = self.data_centre.get_server(server_id)

            server.update_demand(
                demand["cpu_demand"],
                demand["memory_demand"],
            )

        record = {
            "step": self.current_step,
            "scenario": self.workload_generator.scenario,
            "seed": self.workload_generator.seed,
            "state": self.data_centre.snapshot(),
        }

        self._history.append(record)
        self.current_step += 1

        return deepcopy(record)

    def run(self, steps: int) -> list[dict]:
        """Advance the simulation by the requested number of steps."""
        if type(steps) is not int:
            raise TypeError("steps must be an integer.")

        if steps < 0:
            raise ValueError("steps cannot be negative.")

        return [self.step() for _ in range(steps)]

    @property
    def history(self) -> list[dict]:
        """Return recorded states without exposing internal history."""
        return deepcopy(self._history)
