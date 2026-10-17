"""Rate Regime and Duration Risk Management for Tier 2 Sovereign Bonds.

See PROJECT_ROADMAP.md §2.4.1 & Task 7.
"""

from typing import List, Optional, Tuple
import numpy as np


class RateRegimeDetector:
    """Manages duration risk and rate momentum purchase vetoes."""

    def __init__(self, veto_momentum_bps: float = 30.0, zscore_threshold: float = 2.0):
        self.veto_momentum_bps = veto_momentum_bps
        self.zscore_threshold = zscore_threshold
        self.yield_history: List[float] = []

    def update(self, current_yield: float) -> None:
        """Update historical yield buffer."""
        self.yield_history.append(current_yield)

    def is_purchase_vetoed(self, current_yield: float) -> Tuple[bool, str]:
        """Check if rate momentum or z-score vetoes new bond purchases.
        
        Returns (is_vetoed, reason).
        """
        # 7-day rate momentum (168 hours)
        if len(self.yield_history) >= 168:
            yield_7d_ago = self.yield_history[-168]
            momentum_bps = (current_yield - yield_7d_ago) * 10000.0  # converted to bps
            if momentum_bps > self.veto_momentum_bps:
                return True, f"RATE_MOMENTUM_VETO (+{momentum_bps:.1f} bps > +{self.veto_momentum_bps} bps)"

        # 30-day z-score veto (720 hours)
        if len(self.yield_history) >= 720:
            window = self.yield_history[-720:]
            mean_y = float(np.mean(window))
            std_y = float(np.std(window))
            if std_y > 1e-5:
                z = (current_yield - mean_y) / std_y
                if z > self.zscore_threshold:
                    return True, f"RATE_ZSCORE_VETO (z={z:.2f} > {self.zscore_threshold})"

        return False, "RATE_CLEAR"
