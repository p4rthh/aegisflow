"""Unit tests for configuration and constants.

See PROJECT_ROADMAP.md Task 0.
"""

import pytest
from aegisflow.config import AppConfig, get_default_config
from aegisflow.constants import (
    HOURS_PER_YEAR,
    REPO_SWEEP_HOUR,
    REPO_MATURE_HOUR,
    REPO_LOCK_HOURS,
    BREAKEVEN_HOURS_REPO,
    BREAKEVEN_HOURS_BOND,
)
from aegisflow.types import RiskMode


def test_constants():
    assert HOURS_PER_YEAR == 8760
    assert REPO_SWEEP_HOUR == 17
    assert REPO_MATURE_HOUR == 8
    assert REPO_LOCK_HOURS == 15
    # Breakeven durations: h* = haircut / (OD/8760)
    # Repo: 0.005 / (0.12/8760) = 365.0 hours
    assert pytest.approx(BREAKEVEN_HOURS_REPO, rel=1e-3) == 365.0
    # Bond: 0.02 / (0.12/8760) = 1460.0 hours
    assert pytest.approx(BREAKEVEN_HOURS_BOND, rel=1e-3) == 1460.0


def test_default_config_loading():
    cfg = get_default_config()
    assert cfg.aum0 == 3_000_000_000.0
    assert cfg.risk_mode == RiskMode.COST_OPTIMAL
    assert cfg.frictions.tier1_early_redemption_haircut == 0.005
    assert cfg.frictions.tier2_bond_liquidation_haircut == 0.020
    assert cfg.frictions.tier3_stock_liquidation_haircut == 0.150
    assert cfg.frictions.emergency_overdraft_penalty_apr == 0.120
    assert cfg.bond.duration == 1.92


def test_invalid_risk_mode():
    with pytest.raises(Exception):
        AppConfig(risk_mode="invalid_mode")
