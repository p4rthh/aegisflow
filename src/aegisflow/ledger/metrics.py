"""Institutional Treasury Performance Metrics.

See PROJECT_ROADMAP.md §4.2 & Task 2.
"""

from typing import Dict, Any, List
import numpy as np
import pandas as pd
from aegisflow.constants import HOURS_PER_YEAR
from aegisflow.ledger.state import PortfolioState


def compute_metrics(
    state: PortfolioState,
    econ_pnl_series: np.ndarray,
    nav_series: np.ndarray,
    float_series: np.ndarray,
    bond_yield_series: np.ndarray,
    deployed_series: np.ndarray,
    aum0: float,
) -> Dict[str, Any]:
    """Compute institutional performance and efficiency metrics.
    
    See PROJECT_ROADMAP.md §4.2.
    """
    n_hours = len(econ_pnl_series)
    total_net_pnl = float(econ_pnl_series[-1]) if n_hours > 0 else 0.0

    # Float is strategy-independent average customer-funded capital
    mean_float = float(np.mean(float_series)) if n_hours > 0 else aum0
    net_realized_apy_pct = (
        100.0 * (total_net_pnl / mean_float) * (HOURS_PER_YEAR / max(1, n_hours))
        if mean_float > 0 else 0.0
    )

    # Max Drawdown of economic equity curve
    running_max = np.maximum.accumulate(econ_pnl_series)
    drawdowns = running_max - econ_pnl_series
    max_drawdown_usd = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0
    max_drawdown_pct_aum0 = (max_drawdown_usd / aum0) * 100.0 if aum0 > 0 else 0.0

    # Capital Efficiency Ratio: share of Tier-2 carry ceiling captured
    # Ceiling = sum_t (Float_t * y_{2,t} / 8760)
    carry_ceiling = float(np.sum(float_series * (bond_yield_series / HOURS_PER_YEAR)))
    capital_efficiency_ratio = (
        total_net_pnl / carry_ceiling if abs(carry_ceiling) > 1e-6 else 0.0
    )

    # Deployment Ratio: time-average (Repo + Bonds + Equities) / NAV
    valid_nav = np.where(nav_series > 1e-6, nav_series, 1.0)
    deployment_ratios = np.clip(deployed_series / valid_nav, 0.0, 1.0)
    deployment_ratio = float(np.mean(deployment_ratios)) if len(deployment_ratios) > 0 else 0.0

    # Gross income = repo_interest + bond_carry + positive capital PnL
    gross_income = state.cum_repo_interest + state.cum_bond_carry + max(0.0, state.cum_capital_pnl)
    friction_drag = (
        (state.cum_haircuts + state.cum_od_interest) / gross_income
        if gross_income > 1e-6 else 0.0
    )

    # Calmar ratio
    calmar = (total_net_pnl / max_drawdown_usd) if max_drawdown_usd > 1.0 else 0.0

    # Hourly Sharpe (annualized)
    delta_econ = np.diff(econ_pnl_series)
    if len(delta_econ) > 1 and np.std(delta_econ) > 1e-9:
        sharpe = float(np.sqrt(HOURS_PER_YEAR) * np.mean(delta_econ) / np.std(delta_econ))
    else:
        sharpe = 0.0

    return {
        "net_pnl": total_net_pnl,
        "net_apy_pct": net_realized_apy_pct,
        "max_drawdown_usd": max_drawdown_usd,
        "max_drawdown_pct_aum0": max_drawdown_pct_aum0,
        "overdraft": {
            "episodes": state.od_episodes,
            "draws": state.od_draw_count,
            "volume_usd": state.cum_od_draws_usd,
            "peak_usd": state.peak_overdraft,
            "hours": state.od_hours,
            "interest_usd": state.cum_od_interest,
        },
        "haircuts": {
            "total": state.cum_haircuts,
            "tier1": state.cum_haircut_t1,
            "tier2": state.cum_haircut_t2,
            "tier3": state.cum_haircut_t3,
        },
        "capital_efficiency_ratio": capital_efficiency_ratio,
        "deployment_ratio": deployment_ratio,
        "friction_drag": friction_drag,
        "calmar": calmar,
        "sharpe": sharpe,
    }
