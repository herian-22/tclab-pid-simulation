"""Perbandingan P-only, PI, dan PID pada skenario nominal (opsional tapi bernilai tinggi).

Semua controller memakai gains yang sama (Kp=8, Ki=0.08, Kd=12);
  P-only : Ki=0, Kd=0
  PI     : Kd=0
  PID    : lengkap + anti-windup
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
from tclab_pid.metrics import step_metrics  # noqa: E402

params_file = ROOT / "results" / "params.json"
if params_file.exists():
    p = json.loads(params_file.read_text())
    params = PlantParams(p["T_amb"], p["tau"], p["K"], p["theta"])
else:
    params = PlantParams()

KP, KI, KD = 8.0, 0.08, 12.0
DT, T_END = 1.0, 700
T_STEP = 50


def run_sim(pid_obj):
    plant = ThermalPlant(params, DT)
    t = np.arange(0, T_END + DT, DT)
    T, u, sp = np.zeros_like(t), np.zeros_like(t), np.zeros_like(t)
    T[0] = plant.T
    for i in range(len(t) - 1):
        sp[i] = 23.0 if t[i] < T_STEP else 50.0
        u[i]  = pid_obj.update(sp[i], T[i])
        T[i + 1] = plant.step(u[i])
    sp[-1], u[-1] = sp[-2], u[-2]
    return t, sp, T, u


controllers = {
    "P   (Kp=8, Ki=0, Kd=0)":          PID(KP, 0.0, 0.0, DT),
    "PI  (Kp=8, Ki=0.08, Kd=0)":       PID(KP, KI,  0.0, DT),
    "PID (Kp=8, Ki=0.08, Kd=12)":      PID(KP, KI,  KD,  DT),
}
colors = ["steelblue", "darkorange", "seagreen"]
styles = ["--", "-.", "-"]

fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
rows = []
for (label, ctrl), col, ls in zip(controllers.items(), colors, styles):
    t, sp, T, u = run_sim(ctrl)
    lw = 2.5 if "PID" in label else 1.8
    a1.plot(t, T, color=col, lw=lw, ls=ls, label=label)
    a2.plot(t, u, color=col, lw=lw, ls=ls)
    m = step_metrics(t, T, 50.0, T_STEP, T_END, float(T[T_STEP]))
    rows.append({
        "Kontroler": label.split("(")[0].strip(),
        "Overshoot (%)": round(m["overshoot_pct"], 2),
        "Rise time (s)": round(m["rise_time_10_90"], 0),
        "Settling (s)":  round(m["settling_time_2pct"], 0),
        "SSE (degC)":    round(m["steady_state_error"], 4),
        "IAE":           round(m["IAE"], 1),
    })

a1.plot(t, sp, "k:", lw=1.2, label="Setpoint")
a1.set_ylabel("Suhu (degC)")
a1.set_title("Perbandingan P, PI, dan PID pada model TCLab")
a1.grid(True, ls=":", alpha=0.7)
a1.legend(fontsize=9)
a2.set_ylabel("Daya pemanas (%)")
a2.set_xlabel("Waktu (detik)")
a2.grid(True, ls=":", alpha=0.7)
fig.tight_layout()

out = ROOT / "results" / "figures" / "controller_comparison.png"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=200)
plt.close(fig)
print(f"Tersimpan: {out}")

print("\n--- Perbandingan P / PI / PID ---")
for r in rows:
    print(r)

(ROOT / "results" / "controller_comparison.json").write_text(
    json.dumps(rows, indent=2, ensure_ascii=False))
