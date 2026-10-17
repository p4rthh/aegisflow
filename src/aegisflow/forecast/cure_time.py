"""Expected Overdraft Cure-Time Estimation.

See PROJECT_ROADMAP.md §2.2 & Task 6.
Estimates the expected hours T_t(x) until a shortfall of size x is cured by
subsequent inflows or scheduled repo maturities.
"""

from typing import Optional
import numpy as np
from aegisflow.constants import BREAKEVEN_HOURS_BOND


class CureTimeEstimator:
    """Estimates expected overdraft duration T_t(x)."""

    def __init__(self, max_horizon: float = BREAKEVEN_HOURS_BOND):
        self.max_horizon = max_horizon

    def estimate_cure_hours(
        self,
        need: float,
        hour: int,
        pending_repo: float = 0.0,
        expected_hourly_inflow: float = 0.0,
    ) -> float:
        """Estimate expected duration (in hours) of an overdraft draw of size need.
        
        Key institutional facts (§2.2):
          - If the draw occurs overnight (18:00 - 07:00) and pending_repo >= need,
            the draw cures strictly at 08:00 (hours_to_8am).
          - If pending_repo cures part of it, only remainder needs operational inflow.
          - If the deficit is structural (expected_hourly_inflow <= 0 and no repo),
            cure time reaches max_horizon (1,460 hours -> triggers bond liquidation).
        """
        if need <= 0.0:
            return 0.0

        # Calculate hours remaining until 08:00 repo release
        if hour >= 17:
            hours_to_8am = (24 - hour) + 8
        elif hour < 8:
            hours_to_8am = 8 - hour
        else:
            hours_to_8am = 0  # Daytime: repo already matured

        # Case 1: Covered by morning repo maturity
        if hours_to_8am > 0 and pending_repo >= need:
            return float(hours_to_8am)

        # Case 2: Partial repo coverage
        rem_need = max(0.0, need - pending_repo)
        if rem_need <= 0.0:
            return float(hours_to_8am)

        # Case 3: Need operational inflows to cure remainder
        if expected_hourly_inflow > 1000.0:
            cure_hours = hours_to_8am + (rem_need / expected_hourly_inflow)
            return float(min(self.max_horizon, cure_hours))

        # Structural deficit with no incoming cure in sight
        return float(self.max_horizon)
