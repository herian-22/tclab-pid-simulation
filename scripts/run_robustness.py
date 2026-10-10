"""Analisis ketahanan (robustness) PID terhadap variasi parameter plant.

Dua skenario ketahanan:
  1. Variasi penguatan K: nominal, +30%, -30%
  2. Variasi waktu tunda theta: 20 s (nominal fit), 30 s, 40 s
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

# --- Muat parameter identifikasi jika ada ---
params_file = ROOT / "results" / "params.json"
if params_file.exists():
    p = json.loads(params_file.read_text())
    base = PlantParams(p["T_amb"], p["tau"], p["K"], p["theta"])
    print(f"Parameter basis: K={base.K:.4f}, tau={base.tau:.1f}, theta={base.theta:.1f}")
else:
    base = PlantParams()
    print("Parameter basis: default laporan")

KP, KI, KD = 8.0, 0.08, 12.0
DT, T_END = 1.0, 700
T_STEP = 50


def run_sim(params):
    plant = ThermalPlant(params, DT)
    pid   = PID(KP, KI, KD, DT)
    t = np.arange(0, T_END + DT, DT)
    T, u, sp = np.zeros_like(t), np.zeros_like(t), np.zeros_like(t)
    T[0] = plant.T
    for i in range(len(t) - 1):
        sp[i] = 23.0 if t[i] < T_STEP else 50.0
        u[i]  = pid.update(sp[i], T[i])
        T[i + 1] = plant.step(u[i])
    sp[-1], u[-1] = sp[-2], u[-2]
    return t, sp, T, u


# ==========================================================
# Skenario 1: variasi K ± 30%
# ==========================================================
K_cases = {
    f"K = {base.K * 0.7:.3f} (-30%)": PlantParams(base.T_amb, base.tau, base.K * 0.7, base.theta),
    f"K = {base.K:.3f} (nominal)":     base,
    f"K = {base.K * 1.3:.3f} (+30%)": PlantParams(base.T_amb, base.tau, base.K * 1.3, base.theta),
}

fig1, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
colors_k = ["steelblue", "black", "firebrick"]
rows_k = []
for (label, par), col in zip(K_cases.items(), colors_k):
    t, sp, T, u = run_sim(par)
    lw = 2.5 if "nominal" in label else 1.5
    ls = "-" if "nominal" in label else "--"
    a1.plot(t, T, color=col, lw=lw, ls=ls, label=label)
    a2.plot(t, u, color=col, lw=lw, ls=ls)
    m = step_metrics(t, T, 50.0, T_STEP, T_END, float(T[T_STEP]))
    rows_k.append({
        "Kasus": label,
        "Overshoot (%)": round(m["overshoot_pct"], 2),
        "Rise time (s)": round(m["rise_time_10_90"], 0),
        "Settling (s)":  round(m["settling_time_2pct"], 0),
        "SSE (degC)":    round(m["steady_state_error"], 4),
        "IAE":           round(m["IAE"], 1),
    })

a1.plot(t, sp, "k:", lw=1.2, label="Setpoint")
a1.set_ylabel("Suhu (degC)")
a1.set_title(f"Ketahanan PID: variasi K ±30%  (tau={base.tau:.0f} s, theta={base.theta:.1f} s konstan)")
a1.grid(True, ls=":", alpha=0.7)
a1.legend(fontsize=9)
a2.set_ylabel("Daya pemanas (%)")
a2.set_xlabel("Waktu (detik)")
a2.grid(True, ls=":", alpha=0.7)
fig1.tight_layout()
out1 = ROOT / "results" / "figures" / "robustness_K_variation.png"
fig1.savefig(out1, dpi=200)
plt.close(fig1)
print(f"Tersimpan: {out1}")

# Tabel K
print("\n--- Variasi K ---")
for r in rows_k:
    print(r)

# ==========================================================
# Skenario 2: variasi theta
# ==========================================================
theta_nom = max(base.theta, 20.0)   # gunakan minimal 20 s agar ada range
theta_cases = {
    f"theta = {theta_nom:.0f} s (nominal fit)": PlantParams(base.T_amb, base.tau, base.K, theta_nom),
    f"theta = {theta_nom + 10:.0f} s":           PlantParams(base.T_amb, base.tau, base.K, theta_nom + 10),
    f"theta = {theta_nom + 20:.0f} s":           PlantParams(base.T_amb, base.tau, base.K, theta_nom + 20),
}

fig2, (b1, b2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
colors_th = ["black", "darkorange", "crimson"]
rows_th = []
for (label, par), col in zip(theta_cases.items(), colors_th):
    t, sp, T, u = run_sim(par)
    lw = 2.5 if "nominal" in label else 1.5
    ls = "-" if "nominal" in label else "--"
    b1.plot(t, T, color=col, lw=lw, ls=ls, label=label)
    b2.plot(t, u, color=col, lw=lw, ls=ls)
    m = step_metrics(t, T, 50.0, T_STEP, T_END, float(T[T_STEP]))
    rows_th.append({
        "Kasus": label,
        "Overshoot (%)": round(m["overshoot_pct"], 2),
        "Rise time (s)": round(m["rise_time_10_90"], 0),
        "Settling (s)":  round(m["settling_time_2pct"], 0),
        "SSE (degC)":    round(m["steady_state_error"], 4),
        "IAE":           round(m["IAE"], 1),
    })

b1.plot(t, sp, "k:", lw=1.2, label="Setpoint")
b1.set_ylabel("Suhu (degC)")
b1.set_title(f"Ketahanan PID: variasi waktu tunda theta = {theta_nom:.0f}, "
             f"{theta_nom+10:.0f}, {theta_nom+20:.0f} s  (K={base.K:.3f}, tau={base.tau:.0f} s konstan)")
b1.grid(True, ls=":", alpha=0.7)
b1.legend(fontsize=9)
b2.set_ylabel("Daya pemanas (%)")
b2.set_xlabel("Waktu (detik)")
b2.grid(True, ls=":", alpha=0.7)
fig2.tight_layout()
out2 = ROOT / "results" / "figures" / "robustness_theta_variation.png"
fig2.savefig(out2, dpi=200)
plt.close(fig2)
print(f"Tersimpan: {out2}")

# Tabel theta
print("\n--- Variasi theta ---")
for r in rows_th:
    print(r)

# --- Simpan ringkasan ke JSON ---
summary = {"variasi_K": rows_k, "variasi_theta": rows_th}
(ROOT / "results" / "robustness_summary.json").write_text(
    json.dumps(summary, indent=2, ensure_ascii=False))
print(f"\nRingkasan disimpan: {ROOT / 'results' / 'robustness_summary.json'}")
