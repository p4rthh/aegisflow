"""Unit tests for Ledger, Instruments, and Accounting.

See PROJECT_ROADMAP.md Task 2.
"""

import pytest
import numpy as np
from aegisflow.ledger.state import PortfolioState
from aegisflow.ledger.instruments import (
    sweep_repo,
    mature_repo,
    break_repo,
    buy_bond,
    sell_bond,
    buy_equity,
    sell_equity,
    accrue_overdraft_interest,
    draw_overdraft,
    repay_overdraft,
)
from aegisflow.ledger.accounting import compute_nav, compute_economic_pnl, decompose_pnl


def test_repo_sweep_and_maturity():
    # Test (a): $100M swept at 4.1% matures to $100,007,020.55 (±$0.01)
    # Overnight 15 hours at 4.1% (0.041)
    state = PortfolioState(cash=100_000_000.0)
    swept = sweep_repo(state, 100_000_000.0, locked_rate=0.041)
    assert swept == 100_000_000.0
    assert state.cash == 0.0

    principal, interest = mature_repo(state)
    assert principal == 100_000_000.0
    expected_interest = 100_000_000.0 * 0.041 * (15.0 / 8760.0)
    assert pytest.approx(interest, abs=0.01) == 7020.5479
    assert pytest.approx(state.cash, abs=0.01) == 100_007_020.55


def test_repo_break():
    # Test (b): Break $1,000,000 repo -> proceeds $995,000, fee $5,000
    state = PortfolioState(cash=0.0, repo_principal=1_000_000.0)
    proceeds, fee = break_repo(state, 1_000_000.0, haircut=0.005)
    assert proceeds == 995_000.0
    assert fee == 5_000.0
    assert state.cash == 995_000.0
    assert state.repo_principal == 0.0


def test_liquidations():
    # Test (c): sell $1,000,000 bonds -> $980,000; equities -> $850,000
    state = PortfolioState(bond_units=10_000.0)  # at price 100 -> $1,000,000
    proceeds_b, fee_b = sell_bond(state, 1_000_000.0, bond_price=100.0, haircut=0.02)
    assert proceeds_b == 980_000.0
    assert fee_b == 20_000.0
    assert state.bond_units == 0.0

    state2 = PortfolioState(equity_units=200.0)  # at price 5000 -> $1,000,000
    proceeds_e, fee_e = sell_equity(state2, 1_000_000.0, stock_price=5000.0, haircut=0.15)
    assert proceeds_e == 850_000.0
    assert fee_e == 150_000.0
    assert state2.equity_units == 0.0


def test_overdraft_accrual():
    # Test (d): $10M overdraft for 15 h accrues $2,054.79 (±$0.5)
    # Hourly compound: O * (1 + 0.12/8760)^15 - O
    state = PortfolioState(overdraft=10_000_000.0)
    total_interest = 0.0
    for _ in range(15):
        total_interest += accrue_overdraft_interest(state, od_apr=0.12)
    
    expected_accrued = 10_000_000.0 * ((1.0 + 0.12 / 8760.0)**15 - 1.0)
    assert pytest.approx(total_interest, abs=0.50) == 2054.79
    assert pytest.approx(state.cum_od_interest, abs=0.50) == expected_accrued


def test_duration_approximation():
    # Test (e): +50 bp yield move => clean price move dP = -D_mod * dy = -1.92 * 0.0050 = -0.0096 (-0.96%)
    d_mod = 1.92
    dy = 0.0050
    dp_rel = -d_mod * dy
    assert pytest.approx(dp_rel, abs=1e-6) == -0.0096


def test_pnl_conservation():
    # Test (f): conservation check on multiple steps
    state = PortfolioState(cash=100_000_000.0)
    aum0 = 100_000_000.0
    bond_price = 100.0
    stock_price = 5000.0

    # Buy some bonds and equities
    buy_bond(state, 40_000_000.0, bond_price)
    buy_equity(state, 20_000_000.0, stock_price)

    # Price shifts
    new_bond_price = 101.5
    new_stock_price = 4900.0

    # Sell half bonds, half equities
    sell_bond(state, 10_000_000.0, new_bond_price, haircut=0.02)
    sell_equity(state, 5_000_000.0, new_stock_price, haircut=0.15)

    # Accrue some overdraft
    draw_overdraft(state, 2_000_000.0)
    accrue_overdraft_interest(state, od_apr=0.12)

    # Reconcile NAV and decomposed PnL
    nav = compute_nav(state, new_bond_price, new_stock_price)
    econ_pnl = compute_economic_pnl(nav, aum0, cum_net_flow=0.0)
    decomp = decompose_pnl(state, new_bond_price, new_stock_price)

    assert pytest.approx(econ_pnl, abs=1.0) == decomp["net_decomposed_pnl"]
