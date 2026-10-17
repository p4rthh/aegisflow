"""Baseline 1: Naive Greedy (Maximum Headline Yield Chaser).

See PROJECT_ROADMAP.md §4.1 & Task 3.
Sweeps all excess cash into Tier 3 Equities (~10% expected return).
Uses fixed liquidity-rank deficit resolution (cost-blind):
Repo break -> Bonds -> Equities -> Overdraft.
"""

from typing import Any, Dict, List
import pandas as pd
from aegisflow.ledger.state import PortfolioState
from aegisflow.ledger.instruments import buy_equity, repay_overdraft
from aegisflow.strategies.base import BaseStrategy


class Baseline1Greedy(BaseStrategy):
    """Naive Greedy max-yield chasing strategy."""

    def __init__(self):
        super().__init__(name="baseline1_greedy")

    def pre(
        self,
        t: int,
        row: pd.Series,
        state: PortfolioState,
        ctx: Any,
    ) -> List[Dict[str, Any]]:
        # First priority: repay overdraft
        if state.overdraft > 0.0 and state.cash > 0.0:
            repay_overdraft(state, state.cash)

        # Chases maximum headline yield by deploying all free cash into equities
        stock_price = float(row["tier3_stock_index_price"])
        if state.cash > 1000.0:
            buy_equity(state, state.cash, stock_price)

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
            # Need rem dollars net, proceeds = gross * (1 - 0.005)
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
