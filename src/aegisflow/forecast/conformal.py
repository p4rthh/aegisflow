"""Rolling Conformal Calibration for Tail Risk Guarantee.

See PROJECT_ROADMAP.md §2.3.2 & Task 6.
Adjusts residual scale factor kappa_t so that empirical coverage of P99.5
over the trailing window matches or exceeds target coverage.
"""

from typing import List
import numpy as np


class ConformalCalibrator:
    """Maintains rolling coverage calibration for tail quantiles using Adaptive Conformal Inference."""

    def __init__(
        self,
        target_coverage: float = 0.995,
        window: int = 60,
        min_kappa: float = 0.8,
        max_kappa: float = 2.0,
        gamma: float = 0.05,
    ):
        self.target_coverage = target_coverage
        self.target_miscoverage = 1.0 - target_coverage
        self.window = window
        self.min_kappa = min_kappa
        self.max_kappa = max_kappa
        self.gamma = gamma
        self.history_covered: List[bool] = []
        self.current_kappa = 1.0

    def update(self, realized_drain: float, predicted_p995: float) -> float:
        """Record whether actual peak drain was safely covered by predicted P99.5.
        
        Updates and returns rolling kappa using an adaptive-conformal step.
        """
        is_covered = bool(realized_drain <= predicted_p995)
        self.history_covered.append(is_covered)
        if len(self.history_covered) > self.window:
            self.history_covered.pop(0)

        # Adaptive conformal step: miss_indicator = 1 if missed, 0 if covered
        miss_indicator = 0.0 if is_covered else 1.0
        step = self.gamma * (miss_indicator - self.target_miscoverage)
        self.current_kappa = float(np.clip(self.current_kappa + step, self.min_kappa, self.max_kappa))

        return self.current_kappa
