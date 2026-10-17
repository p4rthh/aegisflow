"""Unit tests for Data Engine (loader, validator, calendar).

See PROJECT_ROADMAP.md Task 1.
"""

import pytest
import pandas as pd
from datetime import date
from aegisflow.data.loader import load_dataset, extract_frictions
from aegisflow.data.validator import validate_dataset
from aegisflow.data.calendar import is_heavy_drain_calendar, get_us_holidays_2026


def test_loader_and_validator():
    df = load_dataset()
    summary = validate_dataset(df)
    assert summary["rows"] == 8760
    assert summary["sweep_open_count"] == 365
    assert summary["sweep_mature_count"] == 365

    # Check first row values (deposits $6,660,184.94, repo rate 4.292% -> 0.04292)
    assert pytest.approx(df["deposits_usd"].iloc[0], abs=1.0) == 6660184.94
    assert pytest.approx(df["tier1_repo_rate_apy"].iloc[0], abs=1e-5) == 0.04292

    # Check sign convention: outflow == -net_flow_usd
    assert (df["outflow"] == -df["net_flow_usd"]).all()

    # Check friction extraction
    frictions, d_mod = extract_frictions(df)
    assert pytest.approx(frictions.tier1_early_redemption_haircut, abs=1e-5) == 0.005
    assert pytest.approx(frictions.tier2_bond_liquidation_haircut, abs=1e-5) == 0.020
    assert pytest.approx(frictions.tier3_stock_liquidation_haircut, abs=1e-5) == 0.150
    assert pytest.approx(frictions.emergency_overdraft_penalty_apr, abs=1e-5) == 0.120
    assert pytest.approx(d_mod, abs=1e-5) == 1.92


def test_calendar_classification():
    # 2026-07-03 observed holiday Friday
    ts_july3 = pd.Timestamp("2026-07-03 17:00:00")
    assert is_heavy_drain_calendar(ts_july3) is True

    # Payday bill-pay day: 2026-01-02
    ts_jan2 = pd.Timestamp("2026-01-02 12:00:00")
    assert is_heavy_drain_calendar(ts_jan2) is True

    # Ordinary Wednesday mid-month: 2026-04-08 (Wednesday, dom 8)
    ts_normal = pd.Timestamp("2026-04-08 10:00:00")
    assert is_heavy_drain_calendar(ts_normal) is False
