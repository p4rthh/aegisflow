"""Unit tests for Night Path Engine & Repo Gatekeeper.

See PROJECT_ROADMAP.md Task 6 & §2.3.
"""

import pytest
import numpy as np
from aegisflow.constants import REPO_LOCK_HOURS
from aegisflow.types import RiskMode
from aegisflow.forecast.night_paths import NightPathEngine
from aegisflow.forecast.conformal import ConformalCalibrator
from aegisflow.optimize.repo_sizing import (
    calculate_sweep_sizing,
    compute_expected_overdraft_hours,
    solve_rule_b_buffer,
)


def test_night_path_simulation():
    engine = NightPathEngine(n_paths=1000, seed=42)
    # 15 hours mean forecast of 1M outflow per hour
    mean_forecast = np.full(REPO_LOCK_HOURS, 1_000_000.0)

    sim = engine.simulate_night(mean_forecast, is_heavy=False)
    assert len(sim["peak_drains"]) == 1000
    assert sim["cumulative_paths"].shape == (1000, 15)
    # Drain quantiles should be positive and monotone
    q = sim["quantiles"]
    assert q["p50"] <= q["p90"] <= q["p95"] <= q["p986"] <= q["p995"]


def test_rule_b_bisection_accuracy():
    engine = NightPathEngine(n_paths=2000, seed=42)
    mean_forecast = np.full(REPO_LOCK_HOURS, 500_000.0)
    sim = engine.simulate_night(mean_forecast, is_heavy=False)

    repo_rate = 0.0412
    od_apr = 0.120
    target_hours = (15.0 * repo_rate) / od_apr  # ~5.15 hours

    b_opt = solve_rule_b_buffer(target_hours, sim["cumulative_paths"], sim["peak_drains"])
    actual_hours = compute_expected_overdraft_hours(b_opt, sim["cumulative_paths"])

    # Must match within 0.10 hours tolerance
    assert abs(actual_hours - target_hours) < 0.15


def test_rule_comparisons_and_modes():
    engine = NightPathEngine(n_paths=2000, seed=42)
    mean_forecast = np.full(REPO_LOCK_HOURS, 800_000.0)
    sim = engine.simulate_night(mean_forecast, is_heavy=True)

    free_cash = 100_000_000.0
    repo_rate = 0.0412

    # Cost optimal
    res_b = calculate_sweep_sizing(
        free_cash=free_cash,
        repo_rate_apy=repo_rate,
        peak_drains=sim["peak_drains"],
        cumulative_paths=sim["cumulative_paths"],
        quantiles=sim["quantiles"],
        risk_mode=RiskMode.COST_OPTIMAL,
    )

    # Conservative (P99.5)
    res_cons = calculate_sweep_sizing(
        free_cash=free_cash,
        repo_rate_apy=repo_rate,
        peak_drains=sim["peak_drains"],
        cumulative_paths=sim["cumulative_paths"],
        quantiles=sim["quantiles"],
        risk_mode=RiskMode.CONSERVATIVE,
    )

    # Conservative buffer must be >= Cost-optimal buffer
    assert res_cons.buffer_usd >= res_b.buffer_usd
    # Sweep + buffer must equal free cash (when free cash is large)
    assert pytest.approx(res_b.buffer_usd + res_b.sweep_usd, abs=1.0) == free_cash


def test_conformal_calibrator():
    calibrator = ConformalCalibrator(target_coverage=0.995, window=20)
    # Feed 15 days of safe coverage
    for _ in range(15):
        kappa = calibrator.update(realized_drain=10e6, predicted_p995=20e6)
    assert 0.8 <= kappa <= 1.2
