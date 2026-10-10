# TCLab PID Simulation

PID temperature control simulation on a Temperature Control Lab (TCLab) model.
Plant parameters (K, τ, θ) are identified from a public step-response dataset.

## Project Structure

```
tclab-pid-simulation/
├── data/
│   └── raw/tclab-data.csv      # downloaded by download_data.py
├── src/tclab_pid/
│   ├── model.py                # FOPDT thermal plant model
│   ├── pid.py                  # discrete PID with anti-windup
│   ├── identification.py       # curve-fit K, tau, theta from CSV
│   ├── metrics.py              # overshoot, rise/settling time, IAE
│   └── plotting.py
├── scripts/
│   ├── download_data.py        # 1. download dataset
│   ├── run_identification.py   # 2. identify plant parameters
│   ├── run_simulation.py       # 3. run PID simulation
│   └── run_antiwindup_comparison.py  # 4. compare with/without anti-windup
└── results/                    # auto-generated
    ├── params.json
    ├── metrics.json
    └── figures/
```

## Usage

```bash
pip install -r requirements.txt
python scripts/download_data.py
python scripts/run_identification.py
python scripts/run_simulation.py
```
