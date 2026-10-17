"""Baseline 0: 100% Cash Buffer (Operational Checking Reserves).

See PROJECT_ROADMAP.md §4.1 & Task 3.
Zero yield, zero investments, zero liquidation penalties.
"""

from typing import Any, Dict, List
import pandas as pd
from aegisflow.ledger.state import PortfolioState
from aegisflow.strategies.base import BaseStrategy


class Baseline0Cash(BaseStrategy):
    """100% Cash Buffer benchmark."""

    def __init__(self):
        super().__init__(name="baseline0_cash")

    def pre(
        self,
        t: int,
        row: pd.Series,
        state: PortfolioState,
        ctx: Any,
    ) -> List[Dict[str, Any]]:
        # Never deploy into yield vaults
        return []

    def resolve(
        self,
        t: int,
        shortfall: float,
        row: pd.Series,
        state: PortfolioState,
        ctx: Any,
    ) -> List[Dict[str, Any]]:
        # Has no market assets; must draw emergency overdraft if cash is exhausted
        return [{"source": "OD", "amount": shortfall}]
