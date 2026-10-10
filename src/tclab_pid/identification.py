"""FOPDT parameter identification from a public TCLab step-response dataset."""

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

from .model import PlantParams


def load_dataset(path: str) -> pd.DataFrame:
    """Read CSV (columns: Time, T1, T2, Q1, Q2) and resample to a 1-second grid."""
    df = pd.read_csv(path)
    required = {"Time", "T1", "Q1"}
    if not required.issubset(df.columns):
        raise ValueError(f"Required columns {required}, found {list(df.columns)}")
    df = df.sort_values("Time").drop_duplicates("Time")
    grid = np.arange(0, np.floor(df["Time"].max()) + 1, 1.0)
    out = {"Time": grid}
    for col in df.columns:
        if col != "Time":
            out[col] = np.interp(grid, df["Time"], df[col])
    return pd.DataFrame(out)


def _fopdt_step(t, K, tau, theta, T0, Q):
    dt = np.clip(t - theta, 0.0, None)
    return T0 + K * Q * (1.0 - np.exp(-dt / tau))


def fit_fopdt(df: pd.DataFrame, heater: str = "Q1", sensor: str = "T1"):
    """Fit K, tau, theta to the heater step response (Q constant from start of data).

    Returns (PlantParams, dict with metrics: rmse, T0, Q).
    """
    t = df["Time"].to_numpy()
    T = df[sensor].to_numpy()
    Q = float(np.median(df[heater]))
    T0 = float(np.mean(T[:5]))

    def f(t, K, tau, theta):
        return _fopdt_step(t, K, tau, theta, T0, Q)

    popt, _ = curve_fit(f, t, T, p0=[0.6, 150.0, 2.0],
                        bounds=([0.0, 10.0, 0.0], [5.0, 2000.0, 60.0]))
    K, tau, theta = popt
    rmse = float(np.sqrt(np.mean((f(t, *popt) - T) ** 2)))
    return PlantParams(T_amb=T0, tau=float(tau), K=float(K), theta=float(theta)), \
        {"rmse": rmse, "T0": T0, "Q": Q}
