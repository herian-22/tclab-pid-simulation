"""Step 2: PID simulation. Uses results/params.json if available, otherwise falls back to default values."""

import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from tclab_pid.metrics import step_metrics  # noqa: E402
from tclab_pid.model import PlantParams, ThermalPlant  # noqa: E402
from tclab_pid.pid import PID  # noqa: E402
from tclab_pid.plotting import plot_pid  # noqa: E402

KP, KI, KD = 8.0, 0.08, 12.0
DT, T_END = 1.0, 1200

# Step windows (seconds)
T_STEP1_START, T_STEP1_END = 50, 600   # step 23 -> 50 degC
T_STEP2_START, T_STEP2_END = 600, 1200 # step 50 -> 65 degC

params_file = ROOT / "results" / "params.json"
if params_file.exists():
    p = json.loads(params_file.read_text())
    params = PlantParams(p["T_amb"], p["tau"], p["K"], p["theta"])
    print("Plant parameters: identified from public dataset")
    print(f"  K={params.K:.4f} degC/%  tau={params.tau:.1f} s  "
          f"theta={params.theta:.1f} s  T_amb={params.T_amb:.2f} degC")
else:
    params = PlantParams()
    print("Plant parameters: default values (run run_identification.py to use the public dataset)")
    print(f"  K={params.K:.4f} degC/%  tau={params.tau:.1f} s  "
          f"theta={params.theta:.1f} s  T_amb={params.T_amb:.2f} degC")

t = np.arange(0, T_END + DT, DT)
plant = ThermalPlant(params, DT)
pid = PID(KP, KI, KD, DT)
T, u, sp = np.zeros_like(t), np.zeros_like(t), np.zeros_like(t)
T[0] = plant.T

for i in range(len(t) - 1):
    sp[i] = 23.0 if t[i] < 50 else (50.0 if t[i] < 600 else 65.0)
    u[i] = pid.update(sp[i], T[i])
    T[i + 1] = plant.step(u[i])
sp[-1], u[-1] = sp[-2], u[-2]

fig_dir = ROOT / "results" / "figures"
fig_dir.mkdir(parents=True, exist_ok=True)
plot_pid(t, sp, T, u, fig_dir / "tclab_pid_performance.png")

# T_start: steady temperature just before each step
idx_step1 = int(T_STEP1_START / DT)
idx_step2 = int(T_STEP2_START / DT)
T_start1 = float(T[idx_step1])          # temperature at the start of step 1
T_start2 = float(T[idx_step2])          # temperature at the start of step 2

m1 = step_metrics(t, T, 50.0, T_STEP1_START, T_STEP1_END, T_start1)
m2 = step_metrics(t, T, 65.0, T_STEP2_START, T_STEP2_END, T_start2)

(ROOT / "results" / "metrics.json").write_text(
    json.dumps({"step_23_to_50": m1, "step_50_to_65": m2,
                "pid_gains": {"Kp": KP, "Ki": KI, "Kd": KD}}, indent=2))

print(f"\nPID gains: Kp={KP}, Ki={KI}, Kd={KD}")
print("-" * 65)
for name, m in (("Step 23->50 degC", m1), ("Step 50->65 degC", m2)):
    print(f"\n{name}  [window {m['window_start_s']:.0f}-{m['window_end_s']:.0f} s]")
    for k, v in m.items():
        if k not in ("window_start_s", "window_end_s"):
            print(f"  {k:25s}: {v:.4f}")
print("-" * 65)
print(f"\nFigure saved: {fig_dir / 'tclab_pid_performance.png'}")
print(f"Metrics saved: {ROOT / 'results' / 'metrics.json'}")

