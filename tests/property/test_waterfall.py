"""Property and unit tests for Waterfall Optimizer and LP Verifier.

See PROJECT_ROADMAP.md Task 4 & §3.1.
"""

import pytest
import numpy as np
from aegisflow.ledger.state import PortfolioState
from aegisflow.types import LiquiditySource, CostSource
from aegisflow.optimize.waterfall import compute_source_costs, solve_greedy_waterfall
from aegisflow.optimize.lp_verify import solve_lp_waterfall


def test_overdraft_vs_repo_short_cure():
    # Theorem 1: Short cure (e.g. 15 hours to 08:00 maturity)
    # OD cost = 0.12 * 15 / 8760 = 0.000205 (0.0205%)
    # T1 break cost = 0.005 / 0.995 = 0.005025 (0.5025%) -> 24x more expensive!
    state = PortfolioState(repo_principal=50_000_000.0)
    sources = compute_source_costs(
        need=10_000_000.0,
        state=state,
        cure_time_fn=lambda x: 15.0,  # 15 hours
    )

    plan, cost_table = solve_greedy_waterfall(need=10_000_000.0, sources=sources)
    # Overdraft must be chosen first
    assert plan[0]["source"] == "OD"
    assert plan[0]["net"] == 10_000_000.0


def test_bond_vs_overdraft_long_cure():
    # Theorem 1: Long cure (>= 1,460 hours -> structural deficit)
    # OD cost at 1460h = 0.12 * 1460 / 8760 = 0.020 (2.0%)
    # T2 bond haircut = 0.02 / 0.98 = ~0.0204
    # Beyond 1460h (e.g. 2000 hours), bond sale is strictly cheaper than OD
    state = PortfolioState(bond_units=1_000_000.0)  # $100M bond MV
    sources = compute_source_costs(
        need=10_000_000.0,
        state=state,
        cure_time_fn=lambda x: 2000.0,
    )

    plan, cost_table = solve_greedy_waterfall(need=10_000_000.0, sources=sources)
    # Bond sale must be chosen over OD
    assert plan[0]["source"] == "T2_SELL"


def test_overdraft_cap_binding():
    # When OD is capped at $5M, next cheapest source must take the remainder
    state = PortfolioState(
        overdraft=0.0,
        bond_units=200_000.0,  # $20M bond MV at price 100
    )
    sources = compute_source_costs(
        need=12_000_000.0,
        state=state,
        cure_time_fn=lambda x: 15.0,
        overdraft_cap=5_000_000.0,
    )

    plan, cost_table = solve_greedy_waterfall(need=12_000_000.0, sources=sources)
    assert len(plan) == 2
    assert plan[0]["source"] == "OD"
    assert plan[0]["net"] == 5_000_000.0
    assert plan[1]["source"] == "T2_SELL"
    assert pytest.approx(plan[1]["net"], abs=1e-3) == 7_000_000.0


def test_greedy_vs_lp_optimality():
    # Random instances property test
    np.random.seed(42)
    for _ in range(50):
        need = float(np.random.uniform(1_000_000.0, 50_000_000.0))
        sources = [
            CostSource(source=LiquiditySource.OD, unit_cost=float(np.random.uniform(0.0001, 0.05)), capacity=float(np.random.uniform(5e6, 30e6))),
            CostSource(source=LiquiditySource.T1_BREAK, unit_cost=float(np.random.uniform(0.004, 0.008)), capacity=float(np.random.uniform(5e6, 30e6))),
            CostSource(source=LiquiditySource.T2_SELL, unit_cost=float(np.random.uniform(0.018, 0.025)), capacity=float(np.random.uniform(10e6, 50e6))),
            CostSource(source=LiquiditySource.T3_SELL, unit_cost=float(np.random.uniform(0.14, 0.18)), capacity=float(np.random.uniform(5e6, 30e6))),
        ]

        # Greedy solve
        _, cost_table = solve_greedy_waterfall(need, sources)
        greedy_cost = sum(c["allocated_net"] * c["unit_cost"] for c in cost_table)
        total_allocated = sum(c["allocated_net"] for c in cost_table)

        # LP solve on the exact same allocated amount
        lp_cost, _ = solve_lp_waterfall(total_allocated, sources)

        # Verify greedy matches LP to within numerical tolerance
        assert pytest.approx(greedy_cost, rel=1e-5) == lp_cost
