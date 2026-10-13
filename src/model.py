"""src/model.py — Muat data CSV TCLab dan fit parameter FOPDT (K, tau, theta).

Fungsi utama:
    load_and_fit(csv_path) -> (K, tau, theta, T_amb)
"""

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit


def _fopdt(t, K, tau, theta, T0, Q):
    """Respons suhu model FOPDT terhadap step input Q."""
    dt = np.clip(t - theta, 0.0, None)
    return T0 + K * Q * (1.0 - np.exp(-dt / tau))


def load_and_fit(csv_path: str):
    """Muat CSV dan fit FOPDT dengan least-squares.

    Parameter
    ---------
    csv_path : path ke file tclab-data.csv

    Return
    ------
    (K, tau, theta, T_amb, rmse)
    """
    df = pd.read_csv(csv_path)
    df = df.sort_values("Time").drop_duplicates("Time")

    # Resample ke grid 1 detik agar uniform
    grid = np.arange(0, int(df["Time"].max()) + 1, 1.0)
    t  = grid
    T  = np.interp(grid, df["Time"], df["T1"])
    Q  = float(np.median(df["Q1"]))        # daya step konstan (%)
    T0 = float(np.mean(T[:5]))             # suhu awal sebelum pemanas

    def f(t_, K, tau, theta):
        return _fopdt(t_, K, tau, theta, T0, Q)

    popt, _ = curve_fit(
        f, t, T,
        p0=[0.6, 150.0, 5.0],
        bounds=([0.0, 10.0, 0.0], [5.0, 2000.0, 60.0])
    )
    K, tau, theta = popt
    T_fit = f(t, *popt)
    rmse  = float(np.sqrt(np.mean((T_fit - T) ** 2)))

    return float(K), float(tau), float(theta), float(T0), float(rmse)
