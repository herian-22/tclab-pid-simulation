"""src/tuning.py — Perhitungan gain PID dengan metode Ziegler-Nichols Open-Loop.

Rumus Ziegler-Nichols (reaction-curve / open-loop method):
    Kp = 1.2 * tau / (K * theta)
    Ti = 2 * theta          -> Ki = Kp / Ti
    Td = 0.5 * theta        -> Kd = Kp * Td

Referensi: Ziegler & Nichols (1942), "Optimum Settings for Automatic Controllers".
"""


def ziegler_nichols(K: float, tau: float, theta: float) -> dict:
    """Hitung gain PID dari parameter FOPDT menggunakan Ziegler-Nichols.

    Parameter
    ---------
    K     : Gain statis plant (degC / %)
    tau   : Konstanta waktu (detik)
    theta : Waktu tunda / dead time (detik)

    Return
    ------
    dict berisi Kp, Ki, Kd, Ti, Td
    """
    if theta <= 0:
        raise ValueError("Ziegler-Nichols membutuhkan theta > 0 (waktu tunda tidak boleh nol).")

    Kp = 1.2 * tau / (K * theta)
    Ti = 2.0 * theta          # waktu integral (s)
    Td = 0.5 * theta          # waktu derivatif (s)
    Ki = Kp / Ti
    Kd = Kp * Td

    return {"Kp": Kp, "Ki": Ki, "Kd": Kd, "Ti": Ti, "Td": Td}
