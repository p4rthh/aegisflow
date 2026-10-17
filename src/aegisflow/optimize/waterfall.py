"""Minimum-cost Liquidity Waterfall Engine for Deficit Resolution.

See PROJECT_ROADMAP.md §3.1 & Task 4.
Greedy fractional knapsack solver with dynamic cure-time cost evaluation.
"""

from typing import List, Dict, Any, Optional, Callable, Tuple
import numpy as np
from aegisflow.constants import HOURS_PER_YEAR, REPO_LOCK_HOURS
from aegisflow.ledger.state import PortfolioState
from aegisflow.types import LiquiditySource, CostSource


def compute_source_costs(
    need: float,
    state: PortfolioState,
    cure_time_fn: Optional[Callable[[float], float]],
    od_apr: float = 0.120,
    h1: float = 0.005,
    h2: float = 0.020,
    h3: float = 0.150,
    overdraft_cap: Optional[float] = None,
    bond_price: float = 100.0,
    stock_price: float = 5000.0,
) -> List[CostSource]:
    """Compute available capacities and unit costs (per net dollar delivered).
    
    Unit cost per net dollar delivered:
      - OD: OD * T(need) / 8760
      - T1 Break: h1 / (1 - h1) + forfeited_rate * (elapsed / 15)
      - T2 Bond Sell: h2 / (1 - h2)
      - T3 Equity Sell: h3 / (1 - h3)
    """
    sources: List[CostSource] = []

    # 1. Overdraft Facility
    od_capacity = float("inf") if overdraft_cap is None else max(0.0, overdraft_cap - state.overdraft)
    expected_hours = 15.0  # default overnight bridge if no callable provided
    if cure_time_fn is not None:
        expected_hours = max(0.0, float(cure_time_fn(need)))
    c_od = (od_apr * expected_hours) / HOURS_PER_YEAR
    sources.append(CostSource(source=LiquiditySource.OD, unit_cost=c_od, capacity=od_capacity))

    # 2. Tier 1 Repo Break
    if state.repo_principal > 0.0:
        net_t1_cap = state.repo_principal * (1.0 - h1)
        # Unit cost = fee / net_proceeds + forfeited interest factor
        forfeited_drag = 0.0
        if state.repo_locked_rate > 0.0 and state.repo_elapsed_hours > 0:
            forfeited_drag = state.repo_locked_rate * (state.repo_elapsed_hours / HOURS_PER_YEAR)
        c_t1 = (h1 / (1.0 - h1)) + forfeited_drag
        sources.append(CostSource(source=LiquiditySource.T1_BREAK, unit_cost=c_t1, capacity=net_t1_cap))

    # 3. Tier 2 Bond Liquidation
    bond_mv = state.bond_units * bond_price
    if bond_mv > 0.0:
        net_t2_cap = bond_mv * (1.0 - h2)
        c_t2 = h2 / (1.0 - h2)  # 0.02 / 0.98 = ~0.020408
        sources.append(CostSource(source=LiquiditySource.T2_SELL, unit_cost=c_t2, capacity=net_t2_cap))

    # 4. Tier 3 Equity Liquidation
    equity_mv = state.equity_units * stock_price
    if equity_mv > 0.0:
        net_t3_cap = equity_mv * (1.0 - h3)
        c_t3 = h3 / (1.0 - h3)  # 0.15 / 0.85 = ~0.17647
        sources.append(CostSource(source=LiquiditySource.T3_SELL, unit_cost=c_t3, capacity=net_t3_cap))

    return sources


def solve_greedy_waterfall(
    need: float,
    sources: List[CostSource],
    h1: float = 0.005,
    h2: float = 0.020,
    h3: float = 0.150,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Solve deficit resolution via greedy fractional knapsack.
    
    Tie-breaking rule: ties go to the non-overdraft source (§3.1).
    Returns (execution_plan, cost_table_audit).
    """
    if need <= 0.0:
        return [], []

    # Sort sources by ascending unit cost.
    # Tie-break key: unit_cost first, then non-OD before OD (source != OD has priority on tie)
    sorted_sources = sorted(
        sources,
        key=lambda s: (s.unit_cost, 1 if s.source == LiquiditySource.OD else 0),
    )

    remaining = need
    execution_plan: List[Dict[str, Any]] = []
    cost_table: List[Dict[str, Any]] = []

    for s in sorted_sources:
        cap_val = float(s.capacity)
        if not np.isfinite(cap_val):
            cap_val = 1e18

        cost_entry = {
            "source": s.source.value,
            "unit_cost": float(s.unit_cost),
            "capacity": cap_val,
            "chosen": False,
            "allocated_net": 0.0,
        }

        if remaining > 1e-9 and s.capacity > 1e-9:
            net_allocated = min(remaining, s.capacity)
            s.chosen = True
            s.allocated = net_allocated
            cost_entry["chosen"] = True
            cost_entry["allocated_net"] = float(net_allocated)
            remaining -= net_allocated

            # Convert net cash needed to gross instrument redemption amount
            if s.source == LiquiditySource.T1_BREAK:
                gross_amount = net_allocated / (1.0 - h1)
                execution_plan.append({"source": "T1_BREAK", "amount": gross_amount, "net": net_allocated})
            elif s.source == LiquiditySource.T2_SELL:
                gross_amount = net_allocated / (1.0 - h2)
                execution_plan.append({"source": "T2_SELL", "amount": gross_amount, "net": net_allocated})
            elif s.source == LiquiditySource.T3_SELL:
                gross_amount = net_allocated / (1.0 - h3)
                execution_plan.append({"source": "T3_SELL", "amount": gross_amount, "net": net_allocated})
            elif s.source == LiquiditySource.OD:
                execution_plan.append({"source": "OD", "amount": net_allocated, "net": net_allocated})

        cost_table.append(cost_entry)

    # If shortfall still remains (e.g. overdraft was capped and all assets exhausted),
    # an emergency uncapped draw must absorb the remainder
    if remaining > 1e-9:
        execution_plan.append({"source": "OD", "amount": remaining, "net": remaining})

    return execution_plan, cost_table
