"""Portfolio state data structure and PnL tracking counters.

See PROJECT_ROADMAP.md §1.3, §3.5 & Task 2.
"""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class PortfolioState:
    # Balances
    cash: float = 0.0               # C: Cash buffer in USD
    repo_principal: float = 0.0     # R: Tier 1 overnight repo principal
    repo_locked_rate: float = 0.0   # Locked APY at 17:00 sweep
    repo_elapsed_hours: int = 0     # Hours elapsed since sweep (0..15)
    bond_units: float = 0.0         # U2: Units of 2Y Sovereign Bonds
    equity_units: float = 0.0       # U3: Units of Tier 3 Equities
    overdraft: float = 0.0          # O: Current emergency overdraft balance

    # Cumulative PnL & Cost Components
    cum_repo_interest: float = 0.0
    cum_bond_carry: float = 0.0
    cum_capital_pnl: float = 0.0
    cum_haircuts: float = 0.0
    cum_haircut_t1: float = 0.0
    cum_haircut_t2: float = 0.0
    cum_haircut_t3: float = 0.0
    cum_od_interest: float = 0.0
    cum_purchase_costs: float = 0.0

    # Overdraft Analytics
    cum_od_draws_usd: float = 0.0
    od_draw_count: int = 0
    od_episodes: int = 0
    od_hours: int = 0
    peak_overdraft: float = 0.0
    in_overdraft_episode: bool = False

    # Historical tracking for capital PnL reconciliation
    cum_bond_purchases_usd: float = 0.0
    cum_bond_sales_nominal_usd: float = 0.0
    cum_equity_purchases_usd: float = 0.0
    cum_equity_sales_nominal_usd: float = 0.0

    def copy(self) -> "PortfolioState":
        """Return a deep copy of the portfolio state."""
        return PortfolioState(**self.__dict__)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)
