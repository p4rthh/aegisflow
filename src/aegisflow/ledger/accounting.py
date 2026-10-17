"""Accounting equations, valuations, Float, and PnL decomposition.

See PROJECT_ROADMAP.md §3.5 & Task 2.
"""

from typing import Dict, Any
from aegisflow.constants import HOURS_PER_YEAR
from aegisflow.ledger.state import PortfolioState


def compute_repo_accrued(state: PortfolioState) -> float:
    """Compute accrued repo interest for mark-to-market NAV calculation."""
    if state.repo_principal <= 0.0 or state.repo_elapsed_hours <= 0:
        return 0.0
    return state.repo_principal * state.repo_locked_rate * (state.repo_elapsed_hours / HOURS_PER_YEAR)


def compute_nav(state: PortfolioState, bond_price: float, stock_price: float) -> float:
    """Calculate net asset value (NAV) mark-to-market.
    
    NAV = Cash + RepoPrincipal + RepoAccrued + U2 * P2 + U3 * P3 - Overdraft
    """
    repo_accrued = compute_repo_accrued(state)
    bond_mv = state.bond_units * bond_price
    equity_mv = state.equity_units * stock_price
    return state.cash + state.repo_principal + repo_accrued + bond_mv + equity_mv - state.overdraft


def compute_economic_pnl(nav: float, aum0: float, cum_net_flow: float) -> float:
    """Compute economic PnL excluding customer float injections/draws.
    
    E_t = NAV_t - Float_t = NAV_t - AUM0 - sum(net_flow)
    """
    float_t = aum0 + cum_net_flow
    return nav - float_t


def decompose_pnl(
    state: PortfolioState,
    bond_price: float,
    stock_price: float,
) -> Dict[str, float]:
    """Decompose economic PnL into fundamental drivers.
    
    E_T = sum(RepoInt) + sum(BondCarry) + Delta(MTM2) + Delta(MTM3)
          - sum(Haircuts) - sum(ODint) - PurchaseCosts
    """
    bond_mv = state.bond_units * bond_price
    equity_mv = state.equity_units * stock_price

    # Realized + unrealized capital PnL:
    # Capital PnL = (Current MV + Cumulative Sales Nominal) - Cumulative Purchases
    bond_capital_pnl = (bond_mv + state.cum_bond_sales_nominal_usd) - state.cum_bond_purchases_usd
    equity_capital_pnl = (equity_mv + state.cum_equity_sales_nominal_usd) - state.cum_equity_purchases_usd
    total_capital_pnl = bond_capital_pnl + equity_capital_pnl

    net_decomposed_pnl = (
        state.cum_repo_interest
        + state.cum_bond_carry
        + total_capital_pnl
        - state.cum_haircuts
        - state.cum_od_interest
        - state.cum_purchase_costs
    )

    return {
        "repo_interest": state.cum_repo_interest,
        "bond_carry": state.cum_bond_carry,
        "bond_capital_pnl": bond_capital_pnl,
        "equity_capital_pnl": equity_capital_pnl,
        "total_capital_pnl": total_capital_pnl,
        "haircuts_total": state.cum_haircuts,
        "haircuts_tier1": state.cum_haircut_t1,
        "haircuts_tier2": state.cum_haircut_t2,
        "haircuts_tier3": state.cum_haircut_t3,
        "overdraft_interest": state.cum_od_interest,
        "purchase_costs": state.cum_purchase_costs,
        "net_decomposed_pnl": net_decomposed_pnl,
    }
