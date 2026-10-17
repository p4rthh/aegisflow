"""15-hour Night Path Simulation Engine using Stratified Block Bootstrap.

See PROJECT_ROADMAP.md §2.3.2 & Task 6.
Preserves the 0.695 lag-1 autocorrelation across the 15-hour overnight window (17:00-08:00).
"""

from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd
from aegisflow.constants import REPO_LOCK_HOURS


class NightPathEngine:
    """Simulates 15-hour overnight paths using stratified block bootstrap of residuals."""

    def __init__(self, n_paths: int = 2000, seed: int = 42):
        self.n_paths = n_paths
        self.rng = np.random.default_rng(seed)
        # Store historical 15-vector residuals stratified by calendar class
        self.history_heavy: List[np.ndarray] = []
        self.history_normal: List[np.ndarray] = []

    def update_history(self, residual_vector_15: np.ndarray, is_heavy: bool) -> None:
        """Record realized 15-hour residual vector from past night."""
        if len(residual_vector_15) == REPO_LOCK_HOURS:
            if is_heavy:
                self.history_heavy.append(residual_vector_15.copy())
            else:
                self.history_normal.append(residual_vector_15.copy())

    def simulate_night(
        self,
        mean_forecast_15: np.ndarray,
        is_heavy: bool,
        conformal_scale: float = 1.0,
    ) -> Dict[str, Any]:
        """Simulate n_paths for the 15-hour overnight window.
        
        Returns:
          - peak_drains: 1D array of peak intra-night running drains D = max_k(-S_k)^+
          - terminal_drains: 1D array of terminal net drains -S_15
          - simulated_paths: (n_paths, 15) matrix of cumulative net flows
          - quantiles: dict of key quantiles
        """
        # Determine candidate pool of historical residual vectors
        pool = self.history_heavy if is_heavy else self.history_normal
        if len(pool) < 10:
            # Combine pools if stratified pool is small
            pool = self.history_heavy + self.history_normal

        if len(pool) >= 5:
            # Stratified block bootstrap: draw whole 15-hour vectors
            indices = self.rng.integers(0, len(pool), size=self.n_paths)
            sampled_residuals = np.array([pool[i] for i in indices], dtype=np.float64) * conformal_scale
        else:
            # Prior initialization when history is sparse: calibrated AR(1) simulation
            # std ~ 3.0M, autocorrelation ~ 0.695
            sampled_residuals = np.zeros((self.n_paths, REPO_LOCK_HOURS), dtype=np.float64)
            innovations = self.rng.normal(0.0, 3_000_000.0, size=(self.n_paths, REPO_LOCK_HOURS))
            for k in range(REPO_LOCK_HOURS):
                if k == 0:
                    sampled_residuals[:, k] = innovations[:, k]
                else:
                    sampled_residuals[:, k] = 0.695 * sampled_residuals[:, k - 1] + innovations[:, k]
            sampled_residuals *= conformal_scale

        # Net flow = -(outflow) = -(mean_outflow + residual)
        sim_hourly_net_flows = -(mean_forecast_15 + sampled_residuals)

        # Cumulative net flow at each hour k: S_k = sum_{j<=k} net_flow_j
        sim_cumulative_flows = np.cumsum(sim_hourly_net_flows, axis=1)

        # Peak intra-night running drain: D = max_k(-S_k)^+
        running_drains = np.maximum(0.0, -sim_cumulative_flows)
        peak_drains = np.max(running_drains, axis=1)
        terminal_drains = -sim_cumulative_flows[:, -1]

        quantiles = {
            "p50": float(np.percentile(peak_drains, 50)),
            "p90": float(np.percentile(peak_drains, 90)),
            "p95": float(np.percentile(peak_drains, 95)),
            "p986": float(np.percentile(peak_drains, 98.61)),
            "p995": float(np.percentile(peak_drains, 99.5)),
        }

        return {
            "peak_drains": peak_drains,
            "terminal_drains": terminal_drains,
            "cumulative_paths": sim_cumulative_flows,
            "quantiles": quantiles,
        }
