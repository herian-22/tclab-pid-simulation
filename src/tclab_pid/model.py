"""TCLab thermal plant model: first-order energy balance with optional time delay."""

from collections import deque
from dataclasses import dataclass


@dataclass
class PlantParams:
    T_amb: float = 23.0   # ambient temperature (degC)
    tau: float = 180.0    # time constant (seconds)
    K: float = 0.65       # gain (degC / %)
    theta: float = 0.0    # time delay (seconds)


class ThermalPlant:
    """dT/dt = (T_amb - T + K*u(t - theta)) / tau, diintegrasi dengan Euler."""

    def __init__(self, params: PlantParams, dt: float = 1.0, T0: float | None = None):
        self.p = params
        self.dt = dt
        self.T = params.T_amb if T0 is None else T0
        n_delay = int(round(params.theta / dt))
        self._buffer = deque([0.0] * n_delay, maxlen=n_delay or None) if n_delay else None

    def step(self, u: float) -> float:
        if self._buffer is not None:
            self._buffer.append(u)
            u = self._buffer[0]
        dTdt = (self.p.T_amb - self.T + self.p.K * u) / self.p.tau
        self.T += dTdt * self.dt
        return self.T
