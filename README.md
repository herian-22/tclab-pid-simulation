# TCLab PID Temperature Control Simulation (Ziegler-Nichols)

## Brief

This project simulates a closed-loop PID temperature controller on the **Temperature Control Lab (TCLab)** Arduino-based module. Instead of tuning by hand or guessing parameters, the plant model was identified directly from real open-loop step-response data published by J. C. Kantor (University of Notre Dame). A **First-Order Plus Dead Time (FOPDT)** model was fitted to the dataset using least-squares optimization, and PID gains were then computed analytically using the **Ziegler-Nichols open-loop (reaction curve)** method. The controller includes **anti-windup clamping** to handle actuator saturation gracefully across multiple setpoint changes.

![System Overview](definisi-skematic.png)

## Project Structure

```
tclab-pid-simulation/
├── README.md               # Full project documentation
├── requirements.txt        # Python dependencies
├── data/
│   └── raw/
│       └── tclab-data.csv  # Open-loop step response dataset (800 s, Q1=50%)
├── src/
│   ├── model.py            # FOPDT parameter identification (K, tau, theta, T_amb)
│   ├── tuning.py           # Ziegler-Nichols open-loop gain calculation
│   └── pid.py              # Discrete PID controller with anti-windup clamping
├── run_zn.py               # Single-command pipeline script
└── results/
    └── zn_result.png       # Simulation output plot (temperature + heater power)
```

## How to Run

Just two commands:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the full simulation
python run_zn.py
```

`run_zn.py` handles the entire pipeline automatically:
1. Reads `data/raw/tclab-data.csv` and fits the FOPDT model via least-squares.
2. Computes PID gains $K_p, K_i, K_d$ using Ziegler-Nichols tuning rules.
3. Simulates the closed-loop system across 3 sequential setpoints (400 seconds each).
4. Calculates performance metrics (Rise Time, Settling Time, Overshoot, SSE).
5. Saves the result plot to `results/zn_result.png`.

## 1. System Identification (FOPDT)

The reference dataset comes from a real open-loop step-response experiment (heater power fixed at $Q_1 = 50\%$ for 800 seconds):

**Source:** [J. C. Kantor, University of Notre Dame](https://jckantor.github.io/CBE32338/data/tclab-data.csv)

### Mathematical Model

FOPDT transfer function approximation:
$$G(s) = \frac{K}{\tau s + 1} e^{-\theta s}$$

Time-domain response to a step input $Q$:
$$T(t) = T_{\text{amb}} + K \cdot Q \cdot \left(1 - e^{-(t - \theta)/\tau}\right) \quad \text{for } t \ge \theta$$

### Fitted Parameter Results

| Parameter | Fitted Value | Unit | Physical Meaning |
|-----------|-------------|------|-----------------|
| **K** | **0.6228** | °C/% | Process gain (temperature rise per 1% heater power) |
| **τ** | **167.8** | s | Time constant (speed of thermal response to reach 63.2%) |
| **θ** | **20.2** | s | Dead time / transport delay (heat conduction lag to sensor) |
| **$T_{\text{amb}}$** | **23.81** | °C | Ambient temperature at the time of the experiment |
| **RMSE** | **0.222** | °C | Fit error standard deviation against real data |

> The dead time $\theta = 20.2\text{ s}$ reflects the physical distance between the TIP31C heater transistor and the TMP36 temperature sensor. This is the main stability-limiting factor for this thermal plant — increasing it even modestly causes the system to oscillate under the same gains.

## 2. Controller Design (Ziegler-Nichols Tuning)

Open-loop reaction curve method (Ziegler & Nichols, 1942) for an ideal/parallel PID structure:

| Gain Parameter | Ziegler-Nichols Formula | Computed Value |
|---------------|------------------------|---------------|
| **$K_p$** | $\frac{1.2 \cdot \tau}{K \cdot \theta} = \frac{1.2 \cdot 167.8}{0.6228 \cdot 20.2}$ | **16.02** |
| **$T_i$** (Integral time) | $2.0 \cdot \theta = 2.0 \cdot 20.2$ | **40.4 s** |
| **$T_d$** (Derivative time) | $0.5 \cdot \theta = 0.5 \cdot 20.2$ | **10.1 s** |
| **$K_i$** | $\frac{K_p}{T_i} = \frac{16.02}{40.4}$ | **0.397** |
| **$K_d$** | $K_p \cdot T_d = 16.02 \cdot 10.1$ | **161.61** |

### PID Algorithm and Anti-Windup Clamping

Discrete difference equation implemented in `src/pid.py`:
$$u[k] = K_p \cdot e[k] + K_i \sum e[j] \Delta t + K_d \frac{e[k] - e[k-1]}{\Delta t}$$

- **Actuator saturation:** Heater power is physically constrained to $0 \le u \le 100\%$.
- **Anti-windup clamping:** Integral accumulation is frozen whenever the control signal hits saturation and the error continues pushing in the same direction. This prevents sluggish windup recovery during setpoint transitions.

## 3. Simulation Results

The test scenario evaluates temperature tracking across **three sequential setpoints**: **35°C**, **45°C**, and **55°C** (each held for **400 seconds**). This range stays within the physical capacity of the heater without excessive extrapolation — at 50% power the module saturates around 55°C.

### Terminal Output (`python run_zn.py`)

```
============================================================
1. FOPDT MODEL IDENTIFICATION
   K     = 0.6228 degC/%  (static gain)
   tau   = 167.8 s       (time constant)
   theta = 20.2 s      (dead time)
   T_amb = 23.81 degC   (ambient temperature)
   RMSE  = 0.222 degC   (fit accuracy)
============================================================

2. ZIEGLER-NICHOLS TUNING
   Kp = 16.0159
   Ki = 0.39680  (Ti = 40.4 s)
   Kd = 161.610  (Td = 10.1 s)
   Formula: Kp = 1.2*tau/(K*theta), Ti = 2*theta, Td = 0.5*theta
============================================================

3. SIMULATION RESULTS
        Setpoint   Rise time    Settling   Overshoot       SSE
   SP=  35 degC        27 s       138 s     14.18%   +0.001
   SP=  45 degC        30 s       140 s     12.35%   +0.000
   SP=  55 degC        38 s       147 s      8.86%   +0.000
============================================================

Plot saved: ...\results\zn_result.png
Done.
```

### Performance Metrics

| Setpoint | Time Window | Rise Time (10–90%) | Settling Time (2%) | Overshoot | Steady-State Error |
|----------|-------------|-------------------|--------------------|-----------|-------------------|
| **35 °C** | $t = 50 - 450\text{ s}$ | **27 s** | **138 s** | **14.18%** | $+0.001\text{ °C}$ |
| **45 °C** | $t = 450 - 850\text{ s}$ | **30 s** | **140 s** | **12.35%** | $+0.000\text{ °C}$ |
| **55 °C** | $t = 850 - 1250\text{ s}$ | **38 s** | **147 s** | **8.86%** | $+0.000\text{ °C}$ |

### Response Analysis

1. **Ziegler-Nichols characteristics:** ZN tuning is intentionally aggressive. The observed overshoot of 8–14% is actually below the theoretical ZN design target (~25%), which suggests the thermal system's natural damping is working in our favor.
2. **Steady-state error elimination:** The integral term drives the steady-state error to essentially zero ($e_{ss} \approx 0.00\text{ °C}$) at all three setpoints.
3. **Setpoint transition efficiency:** Anti-windup clamping keeps settling time stable around ~140 s per 10°C step without the sluggish windup recovery typical of unprotected integrators.

## 4. Plots and Hardware

### Simulation Result — ZN Step Response
![ZN Simulation Result](results/zn_result.png)

### Hardware and Wiring
| Wiring Schematic | TCLab Module |
|-----------------|-------------|
| ![Schematic](rangkaian.png) | ![TCLab Module](alatnya.png) |

