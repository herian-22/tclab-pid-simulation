"""Comparison of PID with vs without anti-windup.

Scenario is designed to make integrator windup clearly visible:
  t=50  s : SP = 80 degC  (far above ambient, integrator saturates for a long time)
  t=600 s : SP = 50 degC  (step down; without anti-windup, temperature will undershoot)
"""

import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from tclab_pid.model import PlantParams, ThermalPlant  # noqa: E402
from tclab_pid.pid import PID  # noqa: E402

# --- Load identified parameters if available ---
params_file = ROOT / "results" / "params.json"
if params_file.exists():
    p = json.loads(params_file.read_text())
    params = PlantParams(p["T_amb"], p["tau"], p["K"], p["theta"])
    print("Parameters: from identification")
else:
    params = PlantParams()
    print("Parameters: default values")

KP, KI, KD = 8.0, 0.5, 12.0   # Ki diperbesar agar windup menumpuk lebih cepat
DT, T_END = 1.0, 900


class PIDNoAntiWindup:
    """Discrete PID without anti-windup (integral accumulates freely during saturation)."""
    def __init__(self, Kp, Ki, Kd, dt=1.0, u_min=0.0, u_max=100.0):
        self.Kp, self.Ki, self.Kd = Kp, Ki, Kd
        self.dt = dt
        self.u_min, self.u_max = u_min, u_max
        self.integral = 0.0
        self._prev_error = None

    def update(self, setpoint, measurement):
        error = setpoint - measurement
        derivative = 0.0 if self._prev_error is None else (error - self._prev_error) / self.dt
        self._prev_error = error
        self.integral += error * self.dt           # always update (no clamping)
        u_raw = self.Kp * error + self.Ki * self.integral + self.Kd * derivative
        return float(min(max(u_raw, self.u_min), self.u_max))


def run_sim(pid_obj):
    plant = ThermalPlant(params, DT)
    t = np.arange(0, T_END + DT, DT)
    T, u, sp = np.zeros_like(t), np.zeros_like(t), np.zeros_like(t)
    T[0] = plant.T
    for i in range(len(t) - 1):
        sp[i] = 23.0 if t[i] < 50 else (80.0 if t[i] < 600 else 50.0)
        u[i] = pid_obj.update(sp[i], T[i])
        T[i + 1] = plant.step(u[i])
    sp[-1], u[-1] = sp[-2], u[-2]
    return t, sp, T, u


t, sp, T_aw, u_aw = run_sim(PID(KP, KI, KD, DT))
_, _, T_naw, u_naw = run_sim(PIDNoAntiWindup(KP, KI, KD, DT))

# --- Metrics: overshoot at SP=80, and recovery time to 50 after t=600 ---
# Key windup effect: without AW, temperature may fail to settle even when the plant can reach it
m_aw  = (t >= 50) & (t < 600)
m_rec = (t >= 600)

overshoot_aw  = max(0.0, T_aw[m_aw].max()  - 80.0)
overshoot_naw = max(0.0, T_naw[m_aw].max() - 80.0)

# Recovery time: first time temperature enters ±1°C of SP=50 after t=600
def recovery_time(T_arr):
    idx = np.where(m_rec)[0]
    for i in idx:
        if abs(T_arr[i] - 50.0) <= 1.0:
            return float(t[i] - 600.0)
    return float('nan')

rec_aw  = recovery_time(T_aw)
rec_naw = recovery_time(T_naw)

print(f"Overshoot above SP=80 (with AW)    : {overshoot_aw:.2f} degC")
print(f"Overshoot above SP=80 (without AW) : {overshoot_naw:.2f} degC  <-- windup!")
print(f"Recovery to 50 degC (with AW)      : {rec_aw:.0f} s")
print(f"Recovery to 50 degC (without AW)   : {rec_naw:.0f} s  <-- slow due to windup"
      if not np.isnan(rec_naw) else f"Recovery to 50 degC (without AW)   : >300 s (did not converge within window)")

# --- Plot ---
fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
a1.plot(t, sp,    "k--", lw=1.5, label="Setpoint (SP)")
a1.plot(t, T_aw,  "b-",  lw=2,
        label=f"With anti-windup  (overshoot={overshoot_aw:.2f} degC, recovery={rec_aw:.0f} s)")
a1.plot(t, T_naw, "r-",  lw=2,
        label=(f"Without anti-windup  (overshoot={overshoot_naw:.2f} degC, "
               f"windup causes slow response)"))
a1.axvline(600, color="gray", ls=":", lw=1, label="t=600 s (SP step down)")
a1.set_ylabel("Temperature (degC)")
a1.set_title("PID Comparison: with vs without anti-windup\n"
             "(SP: 23->80 degC at t=50 s, then 80->50 degC at t=600 s)")
a1.grid(True, ls=":", alpha=0.7)
a1.legend(fontsize=9)

a2.plot(t, u_aw,  "b-", lw=2, label="Heater power - with anti-windup")
a2.plot(t, u_naw, "r-", lw=2, label="Heater power - without anti-windup (saturated at 0% longer)")
a2.axvline(600, color="gray", ls=":", lw=1)
a2.set_ylabel("Heater power (%)")
a2.set_xlabel("Time (s)")
a2.grid(True, ls=":", alpha=0.7)
a2.legend(fontsize=9)

fig.tight_layout()
out = ROOT / "results" / "figures" / "antiwindup_comparison.png"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=200)
plt.close(fig)
print(f"Figure saved: {out}")
