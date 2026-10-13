"""src/model.py — Load TCLab CSV data and fit FOPDT parameters (K, tau, theta).

Main function:
    load_and_fit(csv_path) -> (K, tau, theta, T_amb, rmse)
"""

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit


def _fopdt(t, K, tau, theta, T0, Q):
    """FOPDT temperature response to a step input Q."""
    dt = np.clip(t - theta, 0.0, None)
    return T0 + K * Q * (1.0 - np.exp(-dt / tau))


def load_and_fit(csv_path: str):
    """Load the CSV and fit a FOPDT model using least-squares.

    Parameters
    ----------
    csv_path : path to the tclab-data.csv file

    Returns
    -------
    (K, tau, theta, T_amb, rmse)
    """
    df = pd.read_csv(csv_path)
    df = df.sort_values("Time").drop_duplicates("Time")

    # Resample to a uniform 1-second grid
    grid = np.arange(0, int(df["Time"].max()) + 1, 1.0)
    t  = grid
    T  = np.interp(grid, df["Time"], df["T1"])
    Q  = float(np.median(df["Q1"]))        # constant step power (%)
    T0 = float(np.mean(T[:5]))             # initial temperature before heater on

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
