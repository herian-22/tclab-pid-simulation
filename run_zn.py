"""run_zn.py — Run the full TCLab PID pipeline in a single command.

Steps:
  1. Load the CSV data and fit a FOPDT model (K, tau, theta)
  2. Compute PID gains using Ziegler-Nichols tuning
  3. Simulate the PID controller across 3 setpoints:
        35 degC  (t = 50 - 450 s)
        45 degC  (t = 450 - 850 s)
        55 degC  (t = 850 - 1250 s)
  4. Save the plot to results/zn_result.png

Usage:
    python run_zn.py
"""

import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Add src/ to path so modules can be imported directly
ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from model  import load_and_fit   # noqa: E402
from tuning import ziegler_nichols  # noqa: E402
from pid    import PID              # noqa: E402

# ===========================================================================
# 1. MODEL IDENTIFICATION
# ===========================================================================
csv_path = ROOT / "data" / "raw" / "tclab-data.csv"
if not csv_path.exists():
    print("ERROR: data/raw/tclab-data.csv not found.")
    print("Download it with: python -c \"import urllib.request; "
          "urllib.request.urlretrieve('https://jckantor.github.io/CBE32338/data/tclab-data.csv', "
          "'data/raw/tclab-data.csv')\"")
    sys.exit(1)

K, tau, theta, T_amb, rmse = load_and_fit(str(csv_path))

print("=" * 60)
print("1. FOPDT MODEL IDENTIFICATION")
print(f"   K     = {K:.4f} degC/%  (static gain)")
print(f"   tau   = {tau:.1f} s       (time constant)")
print(f"   theta = {theta:.1f} s      (dead time)")
print(f"   T_amb = {T_amb:.2f} degC   (ambient temperature)")
print(f"   RMSE  = {rmse:.3f} degC   (fit accuracy)")
print("=" * 60)

# ===========================================================================
# 2. ZIEGLER-NICHOLS TUNING
# ===========================================================================
gains = ziegler_nichols(K, tau, theta)
Kp, Ki, Kd = gains["Kp"], gains["Ki"], gains["Kd"]

print("\n2. ZIEGLER-NICHOLS TUNING")
print(f"   Kp = {Kp:.4f}")
print(f"   Ki = {Ki:.5f}  (Ti = {gains['Ti']:.1f} s)")
print(f"   Kd = {Kd:.3f}  (Td = {gains['Td']:.1f} s)")
print("   Formula: Kp = 1.2*tau/(K*theta), Ti = 2*theta, Td = 0.5*theta")
print("=" * 60)

# ===========================================================================
# 3. PID SIMULATION
# ===========================================================================
# Setpoint schedule: 400-second windows starting at t=50 s
# t=0..50    : initial condition (T_amb)
# t=50..450  : SP = 35 degC
# t=450..850 : SP = 45 degC
# t=850..1250: SP = 55 degC

DT    = 1.0
T_END = 1250

SETPOINTS = [
    (50,   450,  35.0),
    (450,  850,  45.0),
    (850,  1250, 55.0),
]
SP_COLORS = ["steelblue", "darkorange", "seagreen"]

def get_sp(t_now):
    for t_start, t_end, val in SETPOINTS:
        if t_start <= t_now < t_end:
            return val
    return T_amb   # before t=50


# --- Plant simulation (FOPDT via Euler integration) ---
from collections import deque  # noqa: E402

def make_plant_state(K_, tau_, theta_, T_amb_, dt_):
    """Create FOPDT plant state with a transport-delay buffer."""
    n_delay = max(1, int(round(theta_ / dt_)))
    buf = deque([0.0] * n_delay, maxlen=n_delay)
    T_state = [T_amb_]

    def step(u):
        buf.append(u)
        u_delayed = buf[0]
        dTdt = (T_amb_ - T_state[0] + K_ * u_delayed) / tau_
        T_state[0] += dTdt * dt_
        return T_state[0]

    return T_state, step

T_state, plant_step = make_plant_state(K, tau, theta, T_amb, DT)

pid = PID(Kp, Ki, Kd, DT)
t_arr = np.arange(0, T_END + DT, DT)
T_arr = np.zeros_like(t_arr)
u_arr = np.zeros_like(t_arr)
sp_arr = np.zeros_like(t_arr)

T_arr[0] = T_amb

for i in range(len(t_arr) - 1):
    sp_arr[i]  = get_sp(t_arr[i])
    u_arr[i]   = pid.update(sp_arr[i], T_arr[i])
    T_arr[i+1] = plant_step(u_arr[i])
sp_arr[-1] = sp_arr[-2]
u_arr[-1]  = u_arr[-2]

print("\n3. SIMULATION RESULTS")
print(f"   {'Setpoint':>12}  {'Rise time':>10}  {'Settling':>10}  {'Overshoot':>10}  {'SSE':>8}")
for (t_s, t_e, sp), col in zip(SETPOINTS, SP_COLORS):
    mask = (t_arr >= t_s) & (t_arr < t_e)
    y    = T_arr[mask]
    tt   = t_arr[mask]
    T_start = float(T_arr[int(t_s / DT)])
    delta   = sp - T_start
    if delta > 0:
        cross90 = next((tt[j] - t_s for j in range(len(y))
                        if y[j] >= T_start + 0.9 * delta), float("nan"))
        cross10 = next((tt[j] - t_s for j in range(len(y))
                        if y[j] >= T_start + 0.1 * delta), float("nan"))
        rise = cross90 - cross10 if not (np.isnan(cross90) or np.isnan(cross10)) else float("nan")
    else:
        rise = float("nan")
    band    = 0.02 * abs(delta)
    outside = np.where(np.abs(y - sp) > band)[0]
    settle  = float(tt[outside[-1]] - t_s) if len(outside) else 0.0
    overshoot = max(0.0, (y.max() - sp) / abs(delta) * 100.0) if delta > 0 else 0.0
    sse = float(sp - y[-1])
    print(f"   SP={sp:>4.0f} degC  {rise:>8.0f} s  {settle:>8.0f} s  {overshoot:>8.2f}%  {sse:>+7.3f}")
print("=" * 60)

# ===========================================================================
# 4. PLOT
# ===========================================================================
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True)

# -- Top panel: temperature --
ax1.plot(t_arr, sp_arr, "k--", lw=1.5, label="Setpoint (SP)")
ax1.plot(t_arr, T_arr,  "r-",  lw=2,   label="Temperature T1 (simulation)")

# Shade each setpoint zone
for (t_s, t_e, sp), col in zip(SETPOINTS, SP_COLORS):
    ax1.axvspan(t_s, t_e, alpha=0.06, color=col)
    ax1.axhline(sp, xmin=(t_s / T_END), xmax=(t_e / T_END),
                color=col, lw=1.2, ls=":", alpha=0.8)
    ax1.text((t_s + t_e) / 2, sp + 0.4, f"SP={sp:.0f}°C",
             ha="center", fontsize=8, color=col)

ax1.set_ylabel("Temperature (degC)", fontsize=11)
ax1.set_title(
    f"TCLab PID Simulation — Ziegler-Nichols Tuning\n"
    f"K={K:.3f} degC/%, tau={tau:.0f} s, theta={theta:.1f} s  |  "
    f"Kp={Kp:.2f}, Ki={Ki:.4f}, Kd={Kd:.2f}",
    fontsize=10
)
ax1.grid(True, ls=":", alpha=0.6)
ax1.legend(loc="lower right", fontsize=9)
ax1.set_ylim(T_amb - 2, 60)

# -- Bottom panel: heater power --
ax2.plot(t_arr, u_arr, "b-", lw=1.8, label="Heater power Q1 (%)")
for (t_s, t_e, _), col in zip(SETPOINTS, SP_COLORS):
    ax2.axvspan(t_s, t_e, alpha=0.06, color=col)
ax2.set_ylabel("Power (%)", fontsize=11)
ax2.set_xlabel("Time (seconds)", fontsize=11)
ax2.set_ylim(-5, 105)
ax2.grid(True, ls=":", alpha=0.6)
ax2.legend(loc="upper right", fontsize=9)

fig.tight_layout()

out = ROOT / "results" / "zn_result.png"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=200)
plt.close(fig)

print(f"\nPlot saved: {out}")
print("Done.")
