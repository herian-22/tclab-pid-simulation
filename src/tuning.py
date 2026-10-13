"""src/tuning.py — PID gain calculation using the Ziegler-Nichols Open-Loop method.

Ziegler-Nichols formulas (reaction-curve / open-loop method):
    Kp = 1.2 * tau / (K * theta)
    Ti = 2 * theta          -> Ki = Kp / Ti
    Td = 0.5 * theta        -> Kd = Kp * Td

Reference: Ziegler & Nichols (1942), "Optimum Settings for Automatic Controllers".
"""


def ziegler_nichols(K: float, tau: float, theta: float) -> dict:
    """Compute PID gains from FOPDT parameters using Ziegler-Nichols.

    Parameters
    ----------
    K     : Static plant gain (degC / %)
    tau   : Time constant (seconds)
    theta : Dead time / transport delay (seconds)

    Returns
    -------
    dict containing Kp, Ki, Kd, Ti, Td
    """
    if theta <= 0:
        raise ValueError("Ziegler-Nichols requires theta > 0 (dead time cannot be zero).")

    Kp = 1.2 * tau / (K * theta)
    Ti = 2.0 * theta          # integral time (s)
    Td = 0.5 * theta          # derivative time (s)
    Ki = Kp / Ti
    Kd = Kp * Td

    return {"Kp": Kp, "Ki": Ki, "Kd": Kd, "Ti": Ti, "Td": Td}
