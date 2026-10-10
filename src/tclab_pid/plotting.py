"""Plotting functions for identification and simulation."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def plot_identification(df, T_fit, params, path):
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(df["Time"], df["T1"], "k.", ms=2, label="Data TCLab (T1)")
    ax.plot(df["Time"], T_fit, "r-", lw=2,
            label=f"Fit FOPDT (K={params.K:.3f}, tau={params.tau:.0f} s, theta={params.theta:.1f} s)")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Temperature (°C)")
    ax.set_title("Parameter identification from public TCLab dataset")
    ax.grid(True, ls=":", alpha=0.7)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def plot_pid(t, sp, T, u, path):
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    a1.plot(t, sp, "k--", lw=2, label="Setpoint (SP)")
    a1.plot(t, T, "r-", lw=2, label="Temperature (PV)")
    a1.set_ylabel("Temperature (°C)")
    a1.set_title("PID + anti-windup performance on TCLab model")
    a1.grid(True, ls=":", alpha=0.7)
    a1.legend(loc="lower right")
    a2.plot(t, u, "b-", lw=2, label="Heater power (MV)")
    a2.set_ylabel("Power (%)")
    a2.set_xlabel("Time (s)")
    a2.grid(True, ls=":", alpha=0.7)
    a2.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
