"""Need-Time Ladder for Strategic Capital Allocation.

See PROJECT_ROADMAP.md §2.5 & Task 7.
Sorts capital by when it will be needed based on the structural flow drain.
"""

from typing import Dict, Any, Tuple
import numpy as np
from aegisflow.constants import HOURS_PER_YEAR


class NeedTimeLadder:
    """Manages strategic allocation tiers via the Need-Time inventory model."""

    def __init__(
        self,
        safety_margin: float = 0.10,
        pool_days: int = 3,
        burnin_days: int = 35,
        h2: float = 0.020,
        h3: float = 0.150,
        mu3: float = 0.10,
    ):
        self.safety_margin = safety_margin
        self.pool_days = pool_days
        self.burnin_days = burnin_days
        self.h2 = h2
        self.h3 = h3
        self.mu3 = mu3

    def compute_need_usd(self, tau_hours: float, d_hat: float) -> float:
        """Compute forecast cumulative capital need over horizon tau hours."""
        hourly_drain = max(0.0, -d_hat)
        return hourly_drain * tau_hours * (1.0 + self.safety_margin)

    def compute_breakeven_thresholds(
        self,
        bond_yield: float,
        repo_rate: float,
    ) -> Tuple[float, float]:
        """Compute dynamic breakeven hours tau_b and tau_e (§2.5).
        
        Returns (tau_b_hours, tau_e_hours).
        """
        # Effective liquid pool yield with rolling 15h overnight repo
        liquid_yield = repo_rate * (15.0 / 24.0)
        spread = bond_yield - liquid_yield

        # If spread is negligible (<= 20 bps), holding bonds never amortizes the 2% fee
        if spread <= 0.0020:
            tau_b_hours = float("inf")
        else:
            # tau_b = (h2 / spread) * 8760
            tau_b_hours = (self.h2 / spread) * HOURS_PER_YEAR

        # tau_e for equities vs bonds: (h3 - h2) / (mu3 - y2) in years
        equity_spread = max(0.005, self.mu3 - bond_yield)
        tau_e_years = (self.h3 - self.h2) / equity_spread
        tau_e_hours = tau_e_years * HOURS_PER_YEAR

        return tau_b_hours, tau_e_hours

    def calculate_targets(
        self,
        t: int,
        nav: float,
        d_hat: float,
        bond_yield: float,
        repo_rate: float,
        equity_eligible: bool,
        w_equity_cap: float = 0.15,
        bond_cap: float = 0.80,
    ) -> Dict[str, float]:
        """Compute target dollar allocations for Bonds and Equities.
        
        Burn-in rule: until day 35, bond target is 0 to allow accurate estimation of d_hat.
        """
        day = t // 24
        if day < self.burnin_days:
            return {
                "tau_b_hours": float("inf"),
                "tau_e_hours": float("inf"),
                "pool_req": 50_000_000.0,
                "bond_target": 0.0,
                "equity_target": 0.0,
            }

        tau_b, tau_e = self.compute_breakeven_thresholds(bond_yield, repo_rate)
        need_liquid = self.compute_need_usd(tau_b, d_hat)
        need_permanent = self.compute_need_usd(tau_e, d_hat)

        # Equity target
        equity_target = 0.0
        if equity_eligible and (nav - need_permanent) > 0.0:
            perm_capital = nav - need_permanent
            equity_target = min(w_equity_cap * nav, perm_capital)

        # Bond target
        free_for_bonds = max(0.0, nav - need_liquid - equity_target)
        bond_target = min(bond_cap * nav, free_for_bonds)

        # Pool requirement (08:00 post maturity)
        pool_req = self.compute_need_usd(self.pool_days * 24.0, d_hat)

        return {
            "tau_b_hours": tau_b,
            "tau_e_hours": tau_e,
            "pool_req": pool_req,
            "bond_target": bond_target,
            "equity_target": equity_target,
        }
