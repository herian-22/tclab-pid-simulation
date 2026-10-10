"""Step-response performance metrics (computed from data, not typed manually)."""

import numpy as np


def step_metrics(t, T, sp_final, t_step, t_end, T_start, band=0.02):
    """Compute metrics for a single setpoint change in the window [t_step, t_end).

    Parameters
    ----------
    t        : time array (seconds)
    T        : temperature array (degC)
    sp_final : final setpoint (degC)
    t_step   : step start time (seconds)  -- left edge of window
    t_end    : window end time (seconds)
    T_start  : initial temperature before step (degC)
    band     : settling time tolerance (fraction of delta, default 2 %)

    Returns
    -------
    dict with metrics and window timing info.
    """
    m = (t >= t_step) & (t < t_end)
    tt, y = t[m], T[m]
    delta = sp_final - T_start
    dt = float(tt[1] - tt[0]) if len(tt) > 1 else 1.0

    overshoot = max(0.0, (y.max() - sp_final) / delta * 100.0)

    def first_cross(level):
        idx = np.argmax(y >= level)
        return float(tt[idx] - t_step) if y[idx] >= level else float('nan')

    # rise time relative to t_step
    t10 = first_cross(T_start + 0.1 * delta)
    t90 = first_cross(T_start + 0.9 * delta)

    outside = np.abs(y - sp_final) > band * abs(delta)
    if outside.any():
        last_outside_idx = np.where(outside)[0][-1]
        settle = float(tt[last_outside_idx] - t_step)
    else:
        settle = 0.0

    # IAE from t_step to t_end
    iae_val = float(np.sum(np.abs(sp_final - y)) * dt)

    return {
        "window_start_s": float(t_step),
        "window_end_s": float(t_end),
        "peak_temperature": float(y.max()),
        "overshoot_pct": float(overshoot),
        "rise_time_10_90": float(t90 - t10) if not (np.isnan(t10) or np.isnan(t90)) else float('nan'),
        "settling_time_2pct": settle,
        "steady_state_error": float(sp_final - y[-1]),
        "IAE": iae_val,
    }
