"""CUSUM Flow Regime Detector for Liquidity Runs.

See PROJECT_ROADMAP.md §2.4.3 & Task 7.
Detects persistent structural shifts in withdrawal pressure.
"""

from typing import Tuple
import numpy as np
from aegisflow.types import OverlayState


class FlowRegimeDetector:
    """Detects elevated stress regimes via CUSUM on standardized flow residuals."""

    def __init__(self, k: float = 0.5, h: float = 5.0, cooldown_hours: int = 6):
        self.k = k
        self.h = h
        self.cooldown_hours = cooldown_hours
        self.cusum = 0.0
        self.below_threshold_count = 0
        self.current_state = OverlayState.NORMAL

    def update(
        self,
        actual_outflow: float,
        q50_outflow: float,
        q90_outflow: float,
    ) -> OverlayState:
        """Update CUSUM detector with row t observations."""
        # Estimate local scale from interquantile range: (q90 - q50) / 1.2816
        iqr_scale = max(500_000.0, (q90_outflow - q50_outflow) / 1.2816)
        z = (actual_outflow - q50_outflow) / iqr_scale

        # CUSUM accumulation
        self.cusum = max(0.0, self.cusum + z - self.k)

        if self.current_state == OverlayState.NORMAL:
            if self.cusum > self.h:
                self.current_state = OverlayState.STRESS_ELEVATED
                self.below_threshold_count = 0
        else:  # Already in STRESS_ELEVATED
            if self.cusum < 1.0:
                self.below_threshold_count += 1
                if self.below_threshold_count >= self.cooldown_hours:
                    self.current_state = OverlayState.NORMAL
                    self.below_threshold_count = 0
            else:
                self.below_threshold_count = 0

        return self.current_state
