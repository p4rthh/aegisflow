"""Unit tests for Chaos Injection and Stress Test Runner.

See PROJECT_ROADMAP.md Task 10 & §5.4.
"""

import pytest
import numpy as np
import pandas as pd
from aegisflow.data.loader import load_dataset
from aegisflow.data.stress import apply_stress_shocks
from aegisflow.sim.stress_runner import run_stress_test


@pytest.fixture(scope="module")
def dataset():
    return load_dataset()


def test_stress_shock_transformations(dataset):
    # 1. Rate shock +100 bps
    shocks_rate = {"rate_shock_bps": 100.0, "rate_shock_ramp_hours": 1}
    df_shocked_rate = apply_stress_shocks(dataset, shocks_rate)
    # Check yield shift: +0.0100
    assert pytest.approx(df_shocked_rate["tier2_bond_yield_pct"].iloc[-1] - dataset["tier2_bond_yield_pct"].iloc[-1], abs=1e-5) == 0.0100
    # Clean bond price shift: dP = -D_mod * dy = -1.92 * 0.0100 = -0.0192 (-1.92%)
    p_ratio = df_shocked_rate["tier2_bond_price_index"].iloc[-1] / dataset["tier2_bond_price_index"].iloc[-1]
    assert pytest.approx(p_ratio, abs=1e-4) == 0.9808

    # 2. Equity crash -30%
    shocks_eq = {"equity_crash_pct": -30.0, "equity_crash_hours": 1}
    df_shocked_eq = apply_stress_shocks(dataset, shocks_eq)
    eq_ratio = df_shocked_eq["tier3_stock_index_price"].iloc[-1] / dataset["tier3_stock_index_price"].iloc[-1]
    assert pytest.approx(eq_ratio, abs=1e-4) == 0.7000

    # 3. Withdrawal multiplier 1.5x
    shocks_w = {"withdrawal_multiplier": 1.5}
    df_shocked_w = apply_stress_shocks(dataset, shocks_w)
    total_w_orig = dataset["withdrawals_usd"].sum()
    total_w_shock = df_shocked_w["withdrawals_usd"].sum()
    assert pytest.approx(total_w_shock / total_w_orig, abs=1e-5) == 1.5000


def test_stress_test_runner(dataset):
    shocks = {
        "withdrawal_multiplier": 1.3,
        "rate_shock_bps": 100.0,
        "equity_crash_pct": -25.0,
    }

    res = run_stress_test(shocks, df=dataset, aum0=3_000_000_000.0)
    assert "results" in res
    assert "aegisflow" in res["results"]
    assert "baseline2_static" in res["results"]
    assert "equity_curves" in res
    assert "worst_nights" in res
    assert len(res["worst_nights"]) > 0
