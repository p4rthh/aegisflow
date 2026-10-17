"""17:00 Repo Gatekeeper & Buffer Sizing Engine.

See PROJECT_ROADMAP.md §2.3.3 & Task 6.
Implements Rules A (Break-only), B (Cost-optimal), and C (Guarded/Conservative).
"""

from typing import Dict, Any, Optional
import numpy as np
from aegisflow.constants import HOURS_PER_YEAR, REPO_LOCK_HOURS
from aegisflow.types import RiskMode, GatekeeperResult


def compute_expected_overdraft_hours(buffer_usd: float, cumulative_paths: np.ndarray) -> float:
    """Compute average hours of overdraft incurred under given buffer size B.
    
    cumulative_paths: shape (n_paths, 15) of cumulative net flows S_k.
    Overdraft occurs at step k if -S_k > buffer_usd.
    """
    # Overdraft at step k: -S_k > B
    in_overdraft = (-cumulative_paths) > buffer_usd
    # Sum over the 15 hours per path, then average across all paths
    hours_per_path = np.sum(in_overdraft, axis=1)
    return float(np.mean(hours_per_path))


def solve_rule_b_buffer(
    target_od_hours: float,
    cumulative_paths: np.ndarray,
    peak_drains: np.ndarray,
    low_b: float = 0.0,
    high_b: Optional[float] = None,
    tol: float = 0.05,
) -> float:
    """Solve for cost-optimal buffer B* via bisection such that E[h(B*)] == target_od_hours."""
    if high_b is None:
        high_b = float(np.percentile(peak_drains, 99.9)) + 5_000_000.0

    # If even B=0 has fewer expected hours than target, optimal buffer is 0
    if compute_expected_overdraft_hours(0.0, cumulative_paths) <= target_od_hours:
        return 0.0

    lo = low_b
    hi = high_b
    for _ in range(35):
        mid = (lo + hi) / 2.0
        exp_h = compute_expected_overdraft_hours(mid, cumulative_paths)
        if abs(exp_h - target_od_hours) < tol:
            return mid
        # exp_h is monotone decreasing in buffer size
        if exp_h > target_od_hours:
            lo = mid  # need larger buffer to reduce overdraft hours
        else:
            hi = mid  # buffer is too large, can reduce

    return (lo + hi) / 2.0


def calculate_sweep_sizing(
    free_cash: float,
    repo_rate_apy: float,
    peak_drains: np.ndarray,
    cumulative_paths: np.ndarray,
    quantiles: Dict[str, float],
    risk_mode: RiskMode = RiskMode.COST_OPTIMAL,
    od_apr: float = 0.120,
    h1: float = 0.005,
    guarded_cap: float = 25_000_000.0,
    epsilon: float = 0.005,
    regime: str = "NORMAL",
    calendar_class: str = "normal",
) -> GatekeeperResult:
    """Derive exact cash buffer B and repo sweep S = max(0, free_cash - B).
    
    See §2.3.3:
      - Rule A (Break-only): B_A = Q_98.61%(D)
      - Rule B (Cost-optimal): E[h(B*)] = 15 * r / OD
      - Rule C (Guarded): max(B_B, Q_{1-eps}(D) - K)
      - Rule C (Conservative): K=0, eps=0.5% -> P99.5
    """
    # Target overdraft hours at the margin: 15 * r / OD
    target_od_hours = (REPO_LOCK_HOURS * repo_rate_apy) / od_apr

    # Rule A: Break-only critical fractile (98.61%)
    b_rule_a = quantiles.get("p986", float(np.percentile(peak_drains, 98.61)))

    # Rule B: Overdraft cost-optimal buffer via bisection
    b_rule_b = solve_rule_b_buffer(target_od_hours, cumulative_paths, peak_drains)

    # Rule C: Tail risk guardrails
    q_tail = quantiles.get("p995", float(np.percentile(peak_drains, 99.5)))

    if risk_mode == RiskMode.CONSERVATIVE:
        # Conservative: zero reliance on overdraft (K = 0, P99.5)
        selected_buffer = max(b_rule_b, q_tail)
    elif risk_mode == RiskMode.GUARDED:
        # Guarded: rely on overdraft up to guarded_cap ($25M)
        selected_buffer = max(b_rule_b, q_tail - guarded_cap)
    else:  # COST_OPTIMAL
        selected_buffer = b_rule_b

    # Ensure buffer is non-negative and bounded
    selected_buffer = max(1_000_000.0, selected_buffer)
    sweep_amount = max(0.0, free_cash - selected_buffer)

    exp_od_hours = compute_expected_overdraft_hours(selected_buffer, cumulative_paths)
    p_exceeds = float(np.mean(peak_drains > selected_buffer))

    return GatekeeperResult(
        risk_mode=risk_mode,
        buffer_usd=float(selected_buffer),
        sweep_usd=float(sweep_amount),
        night_drain_quantiles=quantiles,
        expected_overdraft_hours_at_buffer=exp_od_hours,
        target_overdraft_hours=target_od_hours,
        p_drain_exceeds_buffer=p_exceeds,
        regime=regime,
        calendar_class=calendar_class,
    )
