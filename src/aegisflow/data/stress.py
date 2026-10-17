"""Chaos Injection & Stress Shock Transformer.

See PROJECT_ROADMAP.md §5.4 & Task 10.
Pure transformer that applies macro/liquidity stress shocks to the dataset.
"""

from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from aegisflow.constants import DEFAULT_BOND_DURATION


def apply_stress_shocks(df: pd.DataFrame, shocks: Dict[str, Any]) -> pd.DataFrame:
    """Apply macroeconomic and liquidity shock parameters to create a stressed dataset.
    
    Shock parameters:
      - withdrawal_multiplier: float in [0.5, 5.0]
      - deposit_multiplier: float in [0.5, 2.0]
      - window: optional {start: ISO, end: ISO}
      - run_event: optional {start: ISO, duration_hours: int, peak_multiplier: float, decay: 'exponential'|'linear'}
      - rate_shock_bps: float (|bps| <= 500)
      - rate_shock_start: ISO
      - rate_shock_ramp_hours: int
      - equity_crash_pct: float (in [-60.0, 0.0])
      - equity_crash_start: ISO
      - equity_crash_hours: int
    """
    df_shocked = df.copy()
    n_hours = len(df_shocked)
    ts_series = df_shocked["timestamp"]

    # 1. Withdrawal & Deposit Multipliers (Windowed or Full-Year)
    w_mult = float(shocks.get("withdrawal_multiplier", 1.0))
    d_mult = float(shocks.get("deposit_multiplier", 1.0))

    if w_mult != 1.0 or d_mult != 1.0:
        if "window" in shocks and shocks["window"]:
            start_ts = pd.to_datetime(shocks["window"]["start"])
            end_ts = pd.to_datetime(shocks["window"]["end"])
            mask = (ts_series >= start_ts) & (ts_series <= end_ts)
            df_shocked.loc[mask, "withdrawals_usd"] *= w_mult
            df_shocked.loc[mask, "deposits_usd"] *= d_mult
        else:
            df_shocked["withdrawals_usd"] *= w_mult
            df_shocked["deposits_usd"] *= d_mult

    # 2. Sudden Acute Bank Run Event
    run_cfg = shocks.get("run_event")
    if run_cfg:
        start_ts = pd.to_datetime(run_cfg["start"])
        dur = int(run_cfg.get("duration_hours", 12))
        peak_mult = float(run_cfg.get("peak_multiplier", 4.0))
        decay_type = run_cfg.get("decay", "exponential")

        start_idx = int(df_shocked[ts_series >= start_ts].index[0]) if (ts_series >= start_ts).any() else -1
        if start_idx >= 0:
            end_idx = min(n_hours, start_idx + dur)
            for offset, idx in enumerate(range(start_idx, end_idx)):
                if decay_type == "linear":
                    mult = peak_mult - (peak_mult - 1.0) * (offset / max(1, dur))
                else:  # exponential decay
                    half_life = max(1.0, dur / 3.0)
                    mult = 1.0 + (peak_mult - 1.0) * np.exp(-offset / half_life)
                df_shocked.loc[idx, "withdrawals_usd"] *= mult

    # Recompute net flow and outflow
    df_shocked["net_flow_usd"] = df_shocked["deposits_usd"] - df_shocked["withdrawals_usd"]
    df_shocked["outflow"] = -df_shocked["net_flow_usd"]

    # 3. Sovereign Yield Shock and Bond Price Revaluation (dP/P = -D_mod * dy)
    rate_shock_bps = float(shocks.get("rate_shock_bps", 0.0))
    if rate_shock_bps != 0.0:
        dy_total = rate_shock_bps / 10000.0  # converted to decimal fraction
        ramp_hours = max(1, int(shocks.get("rate_shock_ramp_hours", 168)))
        rate_start_ts = pd.to_datetime(shocks.get("rate_shock_start", str(df_shocked["timestamp"].iloc[0])))

        start_idx = int(df_shocked[ts_series >= rate_start_ts].index[0]) if (ts_series >= rate_start_ts).any() else n_hours
        end_idx = min(n_hours, start_idx + ramp_hours)

        # Build ramp multiplier
        dy_ramp = np.zeros(n_hours, dtype=np.float64)
        if start_idx < n_hours:
            ramp_len = end_idx - start_idx
            dy_ramp[start_idx:end_idx] = np.linspace(0.0, dy_total, ramp_len)
            dy_ramp[end_idx:] = dy_total

        d_mod = float(df_shocked["tier2_bond_mod_duration"].iloc[0]) if "tier2_bond_mod_duration" in df_shocked else DEFAULT_BOND_DURATION
        df_shocked["tier2_bond_yield_pct"] += dy_ramp
        # Bond clean price index: dP = -D_mod * dy
        df_shocked["tier2_bond_price_index"] *= (1.0 - d_mod * dy_ramp)
        # Shift repo rate alongside policy rates
        df_shocked["tier1_repo_rate_apy"] = np.maximum(0.0, df_shocked["tier1_repo_rate_apy"] + dy_ramp)

    # 4. Equity Market Crash
    eq_crash_pct = float(shocks.get("equity_crash_pct", 0.0))
    if eq_crash_pct != 0.0:
        crash_fraction = eq_crash_pct / 100.0  # e.g. -0.30
        crash_hours = max(1, int(shocks.get("equity_crash_hours", 240)))
        eq_start_ts = pd.to_datetime(shocks.get("equity_crash_start", str(df_shocked["timestamp"].iloc[0])))

        start_idx = int(df_shocked[ts_series >= eq_start_ts].index[0]) if (ts_series >= eq_start_ts).any() else n_hours
        end_idx = min(n_hours, start_idx + crash_hours)

        crash_multiplier = np.ones(n_hours, dtype=np.float64)
        if start_idx < n_hours:
            ramp_len = end_idx - start_idx
            # Smoothstep ramp: 3x^2 - 2x^3
            t_norm = np.linspace(0.0, 1.0, ramp_len)
            smooth = 3.0 * (t_norm ** 2) - 2.0 * (t_norm ** 3)
            crash_multiplier[start_idx:end_idx] = 1.0 + crash_fraction * smooth
            crash_multiplier[end_idx:] = 1.0 + crash_fraction

        df_shocked["tier3_stock_index_price"] *= crash_multiplier

    return df_shocked
