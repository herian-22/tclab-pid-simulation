"""src/pid.py — Discrete PID controller with anti-windup (clamping method).

Equation:
    u[k] = Kp*e[k] + Ki*sum(e)*dt + Kd*(e[k]-e[k-1])/dt

Anti-windup: integral accumulation is paused when the actuator is saturated
and the error continues pushing in the same saturation direction.
"""


class PID:
    def __init__(self, Kp: float, Ki: float, Kd: float,
                 dt: float = 1.0,
                 u_min: float = 0.0, u_max: float = 100.0):
        self.Kp, self.Ki, self.Kd = Kp, Ki, Kd
        self.dt = dt
        self.u_min, self.u_max = u_min, u_max
        self.integral = 0.0
        self._prev_error = None

    def reset(self):
        """Reset integral state and previous error."""
        self.integral = 0.0
        self._prev_error = None

    def update(self, setpoint: float, measurement: float) -> float:
        error = setpoint - measurement

        # Derivative term (no derivative kick on the first step)
        if self._prev_error is None:
            derivative = 0.0
        else:
            derivative = (error - self._prev_error) / self.dt
        self._prev_error = error

        # Compute raw output
        candidate_integral = self.integral + error * self.dt
        u_raw = (self.Kp * error
                 + self.Ki * candidate_integral
                 + self.Kd * derivative)

        # Clamp to actuator limits
        u = min(max(u_raw, self.u_min), self.u_max)

        # Anti-windup: only update integral if not saturated in the same direction
        saturated     = u != u_raw
        pushing_deeper = ((u_raw > self.u_max and error > 0) or
                          (u_raw < self.u_min and error < 0))
        if not (saturated and pushing_deeper):
            self.integral = candidate_integral

        return u
