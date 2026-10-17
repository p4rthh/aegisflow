"""Abstract base class for treasury management strategies.

See PROJECT_ROADMAP.md §4.1 & Task 3.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import pandas as pd
from aegisflow.ledger.state import PortfolioState


class BaseStrategy(ABC):
    """Abstract Strategy interface."""

    def __init__(self, name: str):
        self.name = name

    def init(self, df: pd.DataFrame, aum0: float, config: Any) -> None:
        """Initialize strategy state before simulation run."""
        pass

    def pre(
        self,
        t: int,
        row: pd.Series,
        state: PortfolioState,
        ctx: Any,
    ) -> List[Dict[str, Any]]:
        """Actions executed in hour t BEFORE net_flow occurs.
        
        Information constraint: decisions at t may only use information through row t-1!
        """
        return []

    def resolve(
        self,
        t: int,
        shortfall: float,
        row: pd.Series,
        state: PortfolioState,
        ctx: Any,
    ) -> List[Dict[str, Any]]:
        """Ordered list of actions to resolve a cash deficit at end of hour t.
        
        Returns list of dicts: [{"source": "T1_BREAK"|"T2_SELL"|"T3_SELL"|"OD", "amount": float}]
        """
        return []

    def post(
        self,
        t: int,
        row: pd.Series,
        state: PortfolioState,
        ctx: Any,
    ) -> None:
        """Post-step callback (update rolling estimators with row t data)."""
        pass
