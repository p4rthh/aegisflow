"""Rolling Conformal Calibration for Tail Risk Guarantee.

See PROJECT_ROADMAP.md §2.3.2 & Task 6.
Adjusts residual scale factor kappa_t so that empirical coverage of P99.5
over the trailing window matches or exceeds target coverage.
"""

from typing import List
import numpy as np


class ConformalCalibrator:
    """Maintains rolling coverage calibration for tail quantiles."""

    def __init__(self, target_coverage: float = 0.995, window: int = 60, min_kappa: float = 0.8, max_kappa: float = 2.0):
        self.target_coverage = target_coverage
        self.window = window
        self.min_kappa = min_kappa
        self.max_kappa = max_kappa
        self.history_covered: List[bool] = []
        self.current_kappa = 1.0

    def update(self, realized_drain: float, predicted_p995: float) -> float:
        """Record whether actual peak drain was safely covered by predicted P99.5.
        
        Updates and returns rolling kappa.
        """
        is_covered = bool(realized_drain <= predicted_p995)
        self.history_covered.append(is_covered)
        if len(self.history_covered) > self.window:
            self.history_covered.pop(0)

        if len(self.history_covered) >= 15:
            empirical_coverage = float(np.mean(self.history_covered))
            # If coverage falls below target, step up scale factor kappa
            coverage_gap = self.target_coverage - empirical_coverage
            if coverage_gap > 0.0:
                self.current_kappa = min(self.max_kappa, self.current_kappa + 0.05)
            elif len(self.history_covered) >= self.window and empirical_coverage >= 1.0:
                self.current_kappa = max(self.min_kappa, self.current_kappa - 0.02)

        return self.current_kappa
