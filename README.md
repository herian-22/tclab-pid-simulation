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

## Analysis Report

Based on further evaluation of the TCLab PID control system, the following critical characteristics were found:

### 1. PI vs PID Controller (Negligible Derivative Effect)
The derivative action has almost no significant impact on the system's performance. Performance metrics show that the PI and PID controllers yield nearly identical results (IAE for PI = **1827.1** vs PID = **1814.6**). Thus, the dominant role in eliminating steady-state error and reaching the setpoint lies entirely within the **integral action**. 

### 2. Sensitivity: Time Delay ($\theta$) vs. Gain ($K$)
The thermal system is highly sensitive and prone to instability due to changes in time delay rather than changes in gain. When the time delay is increased to $\theta = 40$ seconds, the system begins to oscillate, resulting in an **overshoot of 6.65%** and worsening the settling time to **618 seconds**. This proves that transport delay is the main stability limit for this thermal plant.

### 3. Extrapolation Warning on High Setpoints
Testing the system at a setpoint of **65 °C** (and 80 °C in anti-windup tests) is technically far outside the range of the initial identification dataset. The actual maximum temperature in the real-world training data (`tclab-data.csv`) is only around **54.75 °C**. Therefore, the performance simulations at 65 °C and 80 °C are pure **extrapolations** of the linear FOPDT model. In the real world, non-linear heat transfer effects (such as higher natural convection at elevated temperatures) could cause the physical system to behave differently than the simulation predicts.

## Simulation Results

### Parameter Identification
![Parameter Identification](image.png)

### PID Performance & Anti-Windup
![PID Performance](image%20copy.png)

### Robustness & Extrapolation
![Robustness](image%20copy%202.png)
