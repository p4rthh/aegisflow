"""Canonical per-tick engine step execution sequence.

See PROJECT_ROADMAP.md §1.3 & Task 2.
"""

from typing import Any, Dict, List, Optional
import pandas as pd

from aegisflow.constants import (
    REPO_SWEEP_HOUR,
    REPO_MATURE_HOUR,
    DEFAULT_TIER1_HAIRCUT,
    DEFAULT_TIER2_HAIRCUT,
    DEFAULT_TIER3_HAIRCUT,
    DEFAULT_OVERDRAFT_APR,
)
from aegisflow.ledger.state import PortfolioState
from aegisflow.ledger.instruments import (
    mature_repo,
    accrue_bond_carry,
    accrue_overdraft_interest,
    draw_overdraft,
    repay_overdraft,
    break_repo,
    sell_bond,
    sell_equity,
)
from aegisflow.ledger.accounting import compute_nav, compute_economic_pnl


def execute_canonical_step(
    t: int,
    row: pd.Series,
    state: PortfolioState,
    strategy: Any,
    ctx: Any,
    cum_net_flow: float,
    aum0: float,
    od_apr: float = DEFAULT_OVERDRAFT_APR,
    h1: float = DEFAULT_TIER1_HAIRCUT,
    h2: float = DEFAULT_TIER2_HAIRCUT,
    h3: float = DEFAULT_TIER3_HAIRCUT,
) -> Dict[str, Any]:
    """Execute exactly one hourly tick according to the canonical event order (§1.3).
    
    Order:
      1. Repo maturity (if repo_sweep_mature) -> cash
      2. Bond carry credited to cash: U2 * P2 * y2 / 8760
      3. Overdraft interest accrues: O <- O * (1 + OD / 8760)
      4. If repo is active, increment elapsed lock hours
      5. strategy.pre(t, state, ctx) actions executed
      6. Apply customer net_flow_usd to cash
      7. Shortfall resolution: if cash < 0, call strategy.resolve()
         and execute waterfall; remainder draws overdraft
      8. If cash > 0 and O > 0, auto-repay overdraft
      9. Track overdraft episodes and peak
      10. Mark-to-market valuation, record tick state
      11. strategy.post(t, state, ctx)
    """
    bond_price = float(row["tier2_bond_price_index"])
    bond_yield = float(row["tier2_bond_yield_pct"])
    stock_price = float(row["tier3_stock_index_price"])
    net_flow = float(row["net_flow_usd"])
    sweep_mature = bool(row["repo_sweep_mature"])

    # 1. Repo maturity
    matured_principal, matured_interest = 0.0, 0.0
    if sweep_mature and state.repo_principal > 0.0:
        matured_principal, matured_interest = mature_repo(state)

    # 2. Bond carry
    carry_credited = accrue_bond_carry(state, bond_price, bond_yield)

    # 3. Overdraft interest
    od_interest_accrued = accrue_overdraft_interest(state, od_apr)

    # 4. Repo elapsed time tracking
    if state.repo_principal > 0.0:
        state.repo_elapsed_hours += 1

    # 5. Strategy pre-flow actions (rebalance, buys, sells, sweeps)
    pre_actions = strategy.pre(t, row, state, ctx) if hasattr(strategy, "pre") else []

    # 6. Apply customer net flow
    state.cash += net_flow
    new_cum_net_flow = cum_net_flow + net_flow

    # 7. Shortfall resolution
    deficit_resolved = 0.0
    if state.cash < -1e-9:
        shortfall = -state.cash
        resolve_plan = strategy.resolve(t, shortfall, row, state, ctx) if hasattr(strategy, "resolve") else []

        for item in resolve_plan:
            if state.cash >= -1e-9:
                break
            source = item.get("source")
            amount = item.get("amount", 0.0)
            if amount <= 0.0:
                continue

            if source == "T1_BREAK" and state.repo_principal > 0.0:
                proceeds, _ = break_repo(state, amount, haircut=h1)
                deficit_resolved += proceeds
            elif source == "T2_SELL" and state.bond_units > 0.0:
                proceeds, _ = sell_bond(state, amount, bond_price, haircut=h2)
                deficit_resolved += proceeds
            elif source == "T3_SELL" and state.equity_units > 0.0:
                proceeds, _ = sell_equity(state, amount, stock_price, haircut=h3)
                deficit_resolved += proceeds
            elif source == "OD":
                drawn = draw_overdraft(state, amount)
                deficit_resolved += drawn

        # If any shortfall remains, emergency overdraft must absorb it
        if state.cash < -1e-9:
            emergency_draw = -state.cash
            draw_overdraft(state, emergency_draw)

    # 8. Auto-repay overdraft if positive cash exists
    if state.cash > 1e-9 and state.overdraft > 1e-9:
        repay_overdraft(state, state.cash)

    # 9. Overdraft episode tracking
    if state.overdraft > 1e-9:
        state.od_hours += 1
        if not state.in_overdraft_episode:
            state.od_episodes += 1
            state.in_overdraft_episode = True
    else:
        state.in_overdraft_episode = False

    # 10. Valuation & Metrics
    nav = compute_nav(state, bond_price, stock_price)
    econ_pnl = compute_economic_pnl(nav, aum0, new_cum_net_flow)

    # 11. Strategy post-step hook
    if hasattr(strategy, "post"):
        strategy.post(t, row, state, ctx)

    return {
        "index": t,
        "timestamp": row["timestamp"],
        "cash": state.cash,
        "repo_principal": state.repo_principal,
        "bond_mv": state.bond_units * bond_price,
        "equity_mv": state.equity_units * stock_price,
        "overdraft": state.overdraft,
        "nav": nav,
        "econ_pnl": econ_pnl,
        "cum_net_flow": new_cum_net_flow,
    }
