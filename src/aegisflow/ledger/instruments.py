"""Instrument lifecycle actions and accrual operations.

See PROJECT_ROADMAP.md §1.3, §3.5 & Task 2.
"""

from typing import Tuple
from aegisflow.constants import HOURS_PER_YEAR, REPO_LOCK_HOURS
from aegisflow.ledger.state import PortfolioState


def sweep_repo(state: PortfolioState, amount: float, locked_rate: float) -> float:
    """Sweep cash into Tier 1 Overnight Repo facility at 17:00."""
    actual_amount = min(max(0.0, amount), state.cash)
    if actual_amount > 0.0:
        state.cash -= actual_amount
        state.repo_principal += actual_amount
        state.repo_locked_rate = locked_rate
        state.repo_elapsed_hours = 0
    return actual_amount


def mature_repo(state: PortfolioState) -> Tuple[float, float]:
    """Mature overnight repo at 08:00, crediting principal and interest to cash.
    
    Returns (principal, interest_earned).
    """
    if state.repo_principal <= 0.0:
        return 0.0, 0.0

    principal = state.repo_principal
    # Overnight yield on locked 15 hours
    interest = principal * state.repo_locked_rate * (REPO_LOCK_HOURS / HOURS_PER_YEAR)
    
    state.cash += principal + interest
    state.cum_repo_interest += interest
    state.repo_principal = 0.0
    state.repo_locked_rate = 0.0
    state.repo_elapsed_hours = 0
    return principal, interest


def break_repo(state: PortfolioState, gross_amount: float, haircut: float = 0.005) -> Tuple[float, float]:
    """Early redemption of repo principal prior to 08:00 maturity.
    
    gross_amount: principal broken.
    Returns (net_proceeds, fee_paid).
    """
    actual_broken = min(max(0.0, gross_amount), state.repo_principal)
    if actual_broken <= 0.0:
        return 0.0, 0.0

    fee = actual_broken * haircut
    proceeds = actual_broken - fee

    state.repo_principal -= actual_broken
    state.cash += proceeds
    state.cum_haircuts += fee
    state.cum_haircut_t1 += fee

    if state.repo_principal <= 1e-9:
        state.repo_principal = 0.0
        state.repo_locked_rate = 0.0
        state.repo_elapsed_hours = 0

    return proceeds, fee


def buy_bond(state: PortfolioState, amount_usd: float, bond_price: float, cost_bps: float = 0.0) -> float:
    """Purchase 2Y sovereign bonds at current clean price index."""
    fee_rate = cost_bps / 10000.0
    total_needed = amount_usd * (1.0 + fee_rate)
    actual_spend = min(max(0.0, total_needed), state.cash)
    
    if actual_spend <= 0.0 or bond_price <= 0.0:
        return 0.0

    net_investment = actual_spend / (1.0 + fee_rate)
    purchase_fee = actual_spend - net_investment
    units_bought = net_investment / bond_price

    state.cash -= actual_spend
    state.bond_units += units_bought
    state.cum_bond_purchases_usd += net_investment
    state.cum_purchase_costs += purchase_fee
    return net_investment


def sell_bond(state: PortfolioState, gross_usd: float, bond_price: float, haircut: float = 0.020) -> Tuple[float, float]:
    """Liquidate 2Y sovereign bonds at clean price subject to liquidation haircut."""
    current_mv = state.bond_units * bond_price
    actual_gross = min(max(0.0, gross_usd), current_mv)
    if actual_gross <= 0.0 or bond_price <= 0.0:
        return 0.0, 0.0

    fee = actual_gross * haircut
    net_proceeds = actual_gross - fee
    units_sold = actual_gross / bond_price

    state.bond_units -= units_sold
    state.cash += net_proceeds
    state.cum_bond_sales_nominal_usd += actual_gross
    state.cum_haircuts += fee
    state.cum_haircut_t2 += fee

    if state.bond_units < 1e-9:
        state.bond_units = 0.0

    return net_proceeds, fee


def buy_equity(state: PortfolioState, amount_usd: float, stock_price: float, cost_bps: float = 0.0) -> float:
    """Purchase Tier 3 Blue-Chip Equities."""
    fee_rate = cost_bps / 10000.0
    total_needed = amount_usd * (1.0 + fee_rate)
    actual_spend = min(max(0.0, total_needed), state.cash)

    if actual_spend <= 0.0 or stock_price <= 0.0:
        return 0.0

    net_investment = actual_spend / (1.0 + fee_rate)
    purchase_fee = actual_spend - net_investment
    units_bought = net_investment / stock_price

    state.cash -= actual_spend
    state.equity_units += units_bought
    state.cum_equity_purchases_usd += net_investment
    state.cum_purchase_costs += purchase_fee
    return net_investment


def sell_equity(state: PortfolioState, gross_usd: float, stock_price: float, haircut: float = 0.150) -> Tuple[float, float]:
    """Liquidate Tier 3 Equities subject to fire-sale haircut (15%)."""
    current_mv = state.equity_units * stock_price
    actual_gross = min(max(0.0, gross_usd), current_mv)
    if actual_gross <= 0.0 or stock_price <= 0.0:
        return 0.0, 0.0

    fee = actual_gross * haircut
    net_proceeds = actual_gross - fee
    units_sold = actual_gross / stock_price

    state.equity_units -= units_sold
    state.cash += net_proceeds
    state.cum_equity_sales_nominal_usd += actual_gross
    state.cum_haircuts += fee
    state.cum_haircut_t3 += fee

    if state.equity_units < 1e-9:
        state.equity_units = 0.0

    return net_proceeds, fee


def accrue_bond_carry(state: PortfolioState, bond_price: float, bond_yield: float) -> float:
    """Accrue hourly bond carry (coupon accrual) directly credited to cash.
    
    Formula: U2 * P2 * y2 / 8760
    """
    if state.bond_units <= 0.0:
        return 0.0
    hourly_carry = state.bond_units * bond_price * (bond_yield / HOURS_PER_YEAR)
    state.cash += hourly_carry
    state.cum_bond_carry += hourly_carry
    return hourly_carry


def accrue_overdraft_interest(state: PortfolioState, od_apr: float = 0.120) -> float:
    """Compound hourly overdraft interest onto outstanding overdraft balance.
    
    Formula: O <- O * (1 + OD / 8760)
    """
    if state.overdraft <= 0.0:
        return 0.0
    hourly_interest = state.overdraft * (od_apr / HOURS_PER_YEAR)
    state.overdraft += hourly_interest
    state.cum_od_interest += hourly_interest
    return hourly_interest


def draw_overdraft(state: PortfolioState, amount: float) -> float:
    """Draw from emergency overdraft facility into cash buffer."""
    if amount <= 0.0:
        return 0.0
    state.overdraft += amount
    state.cash += amount
    state.cum_od_draws_usd += amount
    state.od_draw_count += 1
    if state.overdraft > state.peak_overdraft:
        state.peak_overdraft = state.overdraft
    return amount


def repay_overdraft(state: PortfolioState, max_amount: float) -> float:
    """Repay outstanding overdraft using cash buffer."""
    if state.overdraft <= 0.0 or state.cash <= 0.0:
        return 0.0
    repay_amount = min(max_amount, state.overdraft, state.cash)
    if repay_amount > 0.0:
        state.cash -= repay_amount
        state.overdraft -= repay_amount
        if state.overdraft < 1e-9:
            state.overdraft = 0.0
    return repay_amount
