"""Baseline 2: Static Institutional (Fixed Allocation Ratios).

See PROJECT_ROADMAP.md §4.1 & Task 3.
Target allocation:
  - 20% Tier 0 Cash Buffer
  - 30% Tier 1 Overnight Repo
  - 30% Tier 2 Sovereign Bonds
  - 20% Tier 3 Growth Equities

Operations:
  - Daily 17:00 repo top-up towards 30% target
  - Daily 08:00 buy-only rebalancing towards bond/equity targets (no sell rebalance)
  - Fixed liquidity-rank deficit resolution: Repo break -> Bonds -> Equities -> Overdraft
"""

from typing import Any, Dict, List
import pandas as pd
from aegisflow.ledger.state import PortfolioState
from aegisflow.ledger.instruments import (
    sweep_repo,
    buy_bond,
    buy_equity,
    repay_overdraft,
)
from aegisflow.ledger.accounting import compute_nav
from aegisflow.strategies.base import BaseStrategy


class Baseline2Static(BaseStrategy):
    """Static 20/30/30/20 Institutional Benchmark."""

    def __init__(
        self,
        target_cash: float = 0.20,
        target_repo: float = 0.30,
        target_bond: float = 0.30,
        target_equity: float = 0.20,
    ):
        super().__init__(name="baseline2_static")
        self.target_cash = target_cash
        self.target_repo = target_repo
        self.target_bond = target_bond
        self.target_equity = target_equity

    def pre(
        self,
        t: int,
        row: pd.Series,
        state: PortfolioState,
        ctx: Any,
    ) -> List[Dict[str, Any]]:
        # 1. Repay overdraft if positive cash exists
        if state.overdraft > 0.0 and state.cash > 0.0:
            repay_overdraft(state, state.cash)

        hour = int(row["hour"])
        bond_price = float(row["tier2_bond_price_index"])
        stock_price = float(row["tier3_stock_index_price"])
        repo_rate = float(row["tier1_repo_rate_apy"])
        nav = compute_nav(state, bond_price, stock_price)

        # Initial deployment at t=0
        if t == 0:
            target_bond_usd = nav * self.target_bond
            target_eq_usd = nav * self.target_equity
            if state.cash > target_bond_usd:
                buy_bond(state, target_bond_usd, bond_price)
            if state.cash > target_eq_usd:
                buy_equity(state, target_eq_usd, stock_price)

        # 08:00 Buy-only rebalance
        if hour == 8 and state.cash > 0.0:
            bond_mv = state.bond_units * bond_price
            eq_mv = state.equity_units * stock_price
            target_bond_usd = nav * self.target_bond
            target_eq_usd = nav * self.target_equity

            # Buy deficit in bonds
            bond_deficit = max(0.0, target_bond_usd - bond_mv)
            if bond_deficit > 0.0 and state.cash > 0.0:
                spend_bond = min(bond_deficit, state.cash * 0.5)
                buy_bond(state, spend_bond, bond_price)

            # Buy deficit in equities
            eq_deficit = max(0.0, target_eq_usd - eq_mv)
            if eq_deficit > 0.0 and state.cash > 0.0:
                spend_eq = min(eq_deficit, state.cash * 0.5)
                buy_equity(state, spend_eq, stock_price)

        # 17:00 Sweep into overnight repo towards 30% target
        if hour == 17 and state.cash > 0.0:
            target_repo_usd = nav * self.target_repo
            sweep_amount = min(target_repo_usd, max(0.0, state.cash - (nav * self.target_cash)))
            if sweep_amount > 0.0:
                sweep_repo(state, sweep_amount, repo_rate)

        return []

    def resolve(
        self,
        t: int,
        shortfall: float,
        row: pd.Series,
        state: PortfolioState,
        ctx: Any,
    ) -> List[Dict[str, Any]]:
        # Fixed liquidity-rank order: Repo Break -> Bond Sell -> Equity Sell -> Overdraft
        plan: List[Dict[str, Any]] = []
        rem = shortfall

        # 1. Repo Break
        if state.repo_principal > 0.0 and rem > 0.0:
            gross = min(state.repo_principal, rem / (1.0 - 0.005))
            plan.append({"source": "T1_BREAK", "amount": gross})
            rem -= gross * (1.0 - 0.005)

        # 2. Bond Sell
        bond_price = float(row["tier2_bond_price_index"])
        bond_mv = state.bond_units * bond_price
        if bond_mv > 0.0 and rem > 0.0:
            gross = min(bond_mv, rem / (1.0 - 0.020))
            plan.append({"source": "T2_SELL", "amount": gross})
            rem -= gross * (1.0 - 0.020)

        # 3. Equity Sell
        stock_price = float(row["tier3_stock_index_price"])
        equity_mv = state.equity_units * stock_price
        if equity_mv > 0.0 and rem > 0.0:
            gross = min(equity_mv, rem / (1.0 - 0.150))
            plan.append({"source": "T3_SELL", "amount": gross})
            rem -= gross * (1.0 - 0.150)

        # 4. Overdraft
        if rem > 0.0:
            plan.append({"source": "OD", "amount": rem})

        return plan
