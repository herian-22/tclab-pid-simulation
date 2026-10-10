"""Discrete-time PID with actuator saturation and anti-windup clamping."""


class PID:
    def __init__(self, Kp: float, Ki: float, Kd: float, dt: float = 1.0,
                 u_min: float = 0.0, u_max: float = 100.0):
        self.Kp, self.Ki, self.Kd = Kp, Ki, Kd
        self.dt = dt
        self.u_min, self.u_max = u_min, u_max
        self.integral = 0.0
        self._prev_error: float | None = None

    def update(self, setpoint: float, measurement: float) -> float:
        error = setpoint - measurement

        # Derivative; no derivative kick on first step
        if self._prev_error is None:
            derivative = 0.0
        else:
            derivative = (error - self._prev_error) / self.dt
        self._prev_error = error

        candidate_integral = self.integral + error * self.dt
        u_raw = (self.Kp * error
                 + self.Ki * candidate_integral
                 + self.Kd * derivative)
        u = min(max(u_raw, self.u_min), self.u_max)

        # Clamping: integral is only updated when not saturated,
        # or when the error is pulling the output away from the saturation limit.
        saturated = u != u_raw
        pushing_deeper = (u_raw > self.u_max and error > 0) or (u_raw < self.u_min and error < 0)
        if not (saturated and pushing_deeper):
            self.integral = candidate_integral
        return u
