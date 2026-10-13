"""run_zn.py — Jalankan seluruh pipeline TCLab PID dalam satu perintah.

Alur:
  1. Muat data CSV dan fit model FOPDT (K, tau, theta)
  2. Hitung gain PID dengan metode Ziegler-Nichols
  3. Simulasikan kontroler PID dengan 3 setpoint:
        35 degC  (t = 50 - 450 s)
        45 degC  (t = 450 - 850 s)
        55 degC  (t = 850 - 1250 s)
  4. Simpan grafik ke results/zn_result.png

Cara pakai:
    python run_zn.py
"""

import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Tambahkan src/ ke path agar bisa import langsung
ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from model  import load_and_fit   # noqa: E402
from tuning import ziegler_nichols  # noqa: E402
from pid    import PID              # noqa: E402

# ===========================================================================
# 1. IDENTIFIKASI MODEL
# ===========================================================================
csv_path = ROOT / "data" / "raw" / "tclab-data.csv"
if not csv_path.exists():
    print("ERROR: data/raw/tclab-data.csv tidak ditemukan.")
    print("Unduh dengan: python -c \"import urllib.request; "
          "urllib.request.urlretrieve('https://jckantor.github.io/CBE32338/data/tclab-data.csv', "
          "'data/raw/tclab-data.csv')\"")
    sys.exit(1)

K, tau, theta, T_amb, rmse = load_and_fit(str(csv_path))

print("=" * 60)
print("1. IDENTIFIKASI MODEL FOPDT")
print(f"   K     = {K:.4f} degC/%  (gain statis)")
print(f"   tau   = {tau:.1f} s       (konstanta waktu)")
print(f"   theta = {theta:.1f} s      (waktu tunda)")
print(f"   T_amb = {T_amb:.2f} degC   (suhu lingkungan)")
print(f"   RMSE  = {rmse:.3f} degC   (akurasi fit)")
print("=" * 60)

# ===========================================================================
# 2. TUNING ZIEGLER-NICHOLS
# ===========================================================================
gains = ziegler_nichols(K, tau, theta)
Kp, Ki, Kd = gains["Kp"], gains["Ki"], gains["Kd"]

print("\n2. TUNING ZIEGLER-NICHOLS")
print(f"   Kp = {Kp:.4f}")
print(f"   Ki = {Ki:.5f}  (Ti = {gains['Ti']:.1f} s)")
print(f"   Kd = {Kd:.3f}  (Td = {gains['Td']:.1f} s)")
print("   Rumus: Kp = 1.2*tau/(K*theta), Ti = 2*theta, Td = 0.5*theta")
print("=" * 60)

# ===========================================================================
# 3. SIMULASI PID
# ===========================================================================
# Jadwal setpoint: setiap tahap 400 detik, mulai dari t=50 s
# t=0..50   : kondisi awal (T_amb)
# t=50..450 : SP = 35 degC
# t=450..850: SP = 45 degC
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
    return T_amb   # sebelum t=50


# --- Simulasi plant (FOPDT via Euler) ---
from collections import deque  # noqa: E402

def make_plant_state(K_, tau_, theta_, T_amb_, dt_):
    """Buat state plant FOPDT dengan time-delay buffer."""
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

print("\n3. HASIL SIMULASI")
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

# -- Panel atas: suhu --
ax1.plot(t_arr, sp_arr, "k--", lw=1.5, label="Setpoint (SP)")
ax1.plot(t_arr, T_arr,  "r-",  lw=2,   label="Suhu T1 (simulasi)")

# Arsir setiap zona setpoint
for (t_s, t_e, sp), col in zip(SETPOINTS, SP_COLORS):
    ax1.axvspan(t_s, t_e, alpha=0.06, color=col)
    ax1.axhline(sp, xmin=(t_s / T_END), xmax=(t_e / T_END),
                color=col, lw=1.2, ls=":", alpha=0.8)
    ax1.text((t_s + t_e) / 2, sp + 0.4, f"SP={sp:.0f}°C",
             ha="center", fontsize=8, color=col)

ax1.set_ylabel("Suhu (degC)", fontsize=11)
ax1.set_title(
    f"Simulasi PID TCLab — Tuning Ziegler-Nichols\n"
    f"K={K:.3f} degC/%, tau={tau:.0f} s, theta={theta:.1f} s  |  "
    f"Kp={Kp:.2f}, Ki={Ki:.4f}, Kd={Kd:.2f}",
    fontsize=10
)
ax1.grid(True, ls=":", alpha=0.6)
ax1.legend(loc="lower right", fontsize=9)
ax1.set_ylim(T_amb - 2, 60)

# -- Panel bawah: daya pemanas --
ax2.plot(t_arr, u_arr, "b-", lw=1.8, label="Daya pemanas Q1 (%)")
for (t_s, t_e, _), col in zip(SETPOINTS, SP_COLORS):
    ax2.axvspan(t_s, t_e, alpha=0.06, color=col)
ax2.set_ylabel("Daya (%)", fontsize=11)
ax2.set_xlabel("Waktu (detik)", fontsize=11)
ax2.set_ylim(-5, 105)
ax2.grid(True, ls=":", alpha=0.6)
ax2.legend(loc="upper right", fontsize=9)

fig.tight_layout()

out = ROOT / "results" / "zn_result.png"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=200)
plt.close(fig)

print(f"\nGrafik tersimpan: {out}")
print("Selesai.")
