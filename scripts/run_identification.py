"""Langkah 1: identifikasi K, tau, theta dari dataset publik -> results/params.json."""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from tclab_pid.identification import _fopdt_step, fit_fopdt, load_dataset  # noqa: E402
from tclab_pid.plotting import plot_identification  # noqa: E402

csv = ROOT / "data" / "raw" / "tclab-data.csv"
if not csv.exists():
    sys.exit(f"Dataset tidak ditemukan: {csv}\nJalankan dulu: python scripts/download_data.py")

df = load_dataset(str(csv))
params, info = fit_fopdt(df)
T_fit = _fopdt_step(df["Time"].to_numpy(), params.K, params.tau, params.theta, info["T0"], info["Q"])

out = ROOT / "results"
(out / "figures").mkdir(parents=True, exist_ok=True)
plot_identification(df, T_fit, params, out / "figures" / "identification_fit.png")
(out / "params.json").write_text(json.dumps(
    {"T_amb": params.T_amb, "tau": params.tau, "K": params.K, "theta": params.theta,
     "rmse_degC": info["rmse"], "heater_step_pct": info["Q"]}, indent=2))
print(f"K={params.K:.4f} degC/%  tau={params.tau:.1f} s  theta={params.theta:.1f} s  "
      f"T_amb={params.T_amb:.2f}  RMSE={info['rmse']:.3f} degC")
