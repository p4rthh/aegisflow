"""Unit tests for Regime Detectors & Need-Time Ladder.

See PROJECT_ROADMAP.md Task 7 & §2.4, §2.5.
"""

import pytest
import numpy as np
from aegisflow.regime.flow_regime import FlowRegimeDetector
from aegisflow.regime.rate_regime import RateRegimeDetector
from aegisflow.regime.equity_regime import EquityRegimeDetector
from aegisflow.optimize.ladder import NeedTimeLadder
from aegisflow.types import OverlayState


def test_need_time_ladder_thresholds():
    ladder = NeedTimeLadder()

    # Baseline market parameters: y = 4.75%, r = 4.055%
    # liquid_yield = 0.04055 * 15 / 24 = 0.025344
    # spread = 0.0475 - 0.025344 = 0.022156
    # tau_b = (0.02 / 0.022156) * 8760 = ~7907 hours
    tau_b, tau_e = ladder.compute_breakeven_thresholds(bond_yield=0.0475, repo_rate=0.04055)
    assert pytest.approx(tau_b, abs=150.0) == 7907.0

    # tau_e: (0.15 - 0.02) / (0.10 - 0.0475) = 0.13 / 0.0525 = ~2.476 years = ~21,691 hours
    assert pytest.approx(tau_e / 8760.0, abs=0.1) == 2.5

    # Spread <= 20 bps -> infinity
    tau_b_flat, _ = ladder.compute_breakeven_thresholds(bond_yield=0.0260, repo_rate=0.0400)
    assert np.isinf(tau_b_flat)


def test_rate_momentum_veto():
    detector = RateRegimeDetector(veto_momentum_bps=30.0)

    # 168 hours of constant 4.80% yield
    for _ in range(168):
        detector.update(0.0480)

    # +29 bps jump -> should NOT veto
    vetoed_29, _ = detector.is_purchase_vetoed(0.0480 + 0.0029)
    assert vetoed_29 is False

    # +31 bps jump -> MUST veto
    vetoed_31, reason = detector.is_purchase_vetoed(0.0480 + 0.0031)
    assert vetoed_31 is True
    assert "RATE_MOMENTUM_VETO" in reason


def test_cusum_flow_detector():
    detector = FlowRegimeDetector(k=0.5, h=5.0)

    # Normal fluctuations: z ~ 0
    for _ in range(50):
        state = detector.update(actual_outflow=1e6, q50_outflow=1e6, q90_outflow=2e6)
        assert state == OverlayState.NORMAL

    # Acute shock: 4-sigma surge
    for _ in range(5):
        state = detector.update(actual_outflow=6e6, q50_outflow=1e6, q90_outflow=2e6)

    # Must trigger elevated stress
    assert state == OverlayState.STRESS_ELEVATED


def test_equity_regime_realized_vol():
    detector = EquityRegimeDetector()
    np.random.seed(42)
    p = 5000.0

    # Simulate random walk with ~20% annualized vol
    for _ in range(100):
        # hourly std ~ 0.20 / sqrt(8760) ~ 0.002137
        ret = np.random.normal(0.0, 0.002137)
        p *= np.exp(ret)
        vol = detector.update(p)

    # Realized vol should be around 20% +/- 5%
    assert 0.15 <= vol <= 0.28
