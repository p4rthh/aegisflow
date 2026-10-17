"""Meta, configuration, health, and quantitative theorem endpoints.

See PROJECT_ROADMAP.md §5.1, §5.7 & Task 11.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from aegisflow.api.schemas import HealthResponse
from aegisflow.api.deps import AppState, get_app_state
from aegisflow.constants import HOURS_PER_YEAR

router = APIRouter(tags=["Metadata & Theorems"])


@router.get("/health", response_model=HealthResponse)
def health_check(state: AppState = Depends(get_app_state)):
    return {
        "status": "healthy" if state.ready else "initializing",
        "version": "0.1.0",
        "dataset_hours": len(state.df) if state.df is not None else 0,
        "artifacts_ready": state.ready,
    }


@router.get("/meta/config")
def get_config(state: AppState = Depends(get_app_state)):
    cfg = state.config
    return {
        "aum0": cfg.aum0,
        "risk_mode": cfg.risk_mode.value,
        "frictions": {
            "tier1_early_redemption_haircut_pct": cfg.frictions.tier1_early_redemption_haircut * 100.0,
            "tier2_bond_liquidation_haircut_pct": cfg.frictions.tier2_bond_liquidation_haircut * 100.0,
            "tier3_stock_liquidation_haircut_pct": cfg.frictions.tier3_stock_liquidation_haircut * 100.0,
            "emergency_overdraft_penalty_apr_pct": cfg.frictions.emergency_overdraft_penalty_apr * 100.0,
        },
        "bond": {
            "duration": cfg.bond.duration,
            "momentum_veto_bps": cfg.bond_momentum_veto_bps,
        },
        "equity": {
            "w_cap": cfg.equity.w_cap,
            "gate_vol_max": cfg.equity.gate_vol_max,
            "dd_gate": cfg.equity.dd_gate,
            "breaker": cfg.equity.breaker,
            "permanent_horizon_years": cfg.equity.permanent_horizon_years,
        },
        "strategies": [
            {"id": "baseline0_cash", "name": "100% Cash Buffer (Operational Checking)", "description": "Zero yield, zero risk"},
            {"id": "baseline1_greedy", "name": "Naive Greedy (Max Yield Chaser)", "description": "100% equity sweeps, hit by massive haircuts"},
            {"id": "baseline2_static", "name": "Static Institutional (20/30/30/20)", "description": "Fixed ratio allocation"},
            {"id": "aegisflow", "name": "AegisFlow (Dynamic Quantile Waterfall)", "description": "Autonomous need-time ladder with regime awareness"},
        ],
        "assumptions": {
            "aum0_rationale": "Structural net flow drain is -$2.53B/yr; treasury requires minimum $2.6B liquid inventory to avoid permanent insolvency",
            "canonical_order": "Event order strictly adheres to §1.3 with 08:00 maturity, 17:00 sweep, and end-of-hour deficit settlement",
        },
    }


@router.get("/theorems")
def get_theorems(state: AppState = Depends(get_app_state)):
    """Live quantitative break-even calculations for the Stitch UI 'Why' explanation panel."""
    od_apr = state.config.frictions.emergency_overdraft_penalty_apr
    h1 = state.config.frictions.tier1_early_redemption_haircut
    h2 = state.config.frictions.tier2_bond_liquidation_haircut
    h3 = state.config.frictions.tier3_stock_liquidation_haircut

    # Theorem 1: Break-even durations
    h_star_repo = (h1 / od_apr) * HOURS_PER_YEAR    # 365.0 hours
    h_star_bond = (h2 / od_apr) * HOURS_PER_YEAR    # 1,460.0 hours
    h_star_equity = (h3 / od_apr) * HOURS_PER_YEAR  # 10,950.0 hours

    # 15-hour overnight comparison
    overdraft_15h_cost_pct = (od_apr * 15.0 / HOURS_PER_YEAR) * 100.0  # ~0.0205%
    repo_break_cost_pct = h1 * 100.0  # 0.50%
    ratio = repo_break_cost_pct / overdraft_15h_cost_pct  # ~24.4x

    # Theorem 2: Equities vs Bonds breakeven horizon
    mu3 = 0.10
    y2 = 0.0475
    tau_e_years = (h3 - h2) / (mu3 - y2)  # ~2.476 years

    # Theorem 3: Bonds vs Liquid Pool breakeven
    r1 = 0.04055
    liquid_yield = r1 * (15.0 / 24.0)  # ~2.534%
    bond_spread = y2 - liquid_yield    # ~2.216%
    tau_b_hours = (h2 / bond_spread) * HOURS_PER_YEAR  # ~7,907 hours (10.8 months)

    return {
        "theorem_1_overdraft_bridge": {
            "title": "Overdraft Bridge Dominance",
            "overnight_15h_overdraft_cost_pct": overdraft_15h_cost_pct,
            "repo_early_break_fee_pct": repo_break_cost_pct,
            "ratio_cheaper": ratio,
            "breakeven_hours": {
                "repo_break_hours": h_star_repo,
                "bond_liquidation_hours": h_star_bond,
                "equity_liquidation_hours": h_star_equity,
            },
            "insight": f"For any transient overnight shortfall that cures at 08:00, emergency overdraft is {ratio:.1f}x cheaper than cracking Tier 1 Repo early.",
        },
        "theorem_2_equity_horizon": {
            "title": "Permanent Capital Horizon for Equities",
            "breakeven_horizon_years": tau_e_years,
            "insight": f"Due to {h3 * 100:.1f}% fire-sale slippage, equities require an uninterrupted {tau_e_years:.1f}-year holding period to outperform bonds. With a $2.5B/yr net drain, optimal equity allocation is strictly 0 at $3B AUM.",
        },
        "theorem_3_bond_need_time": {
            "title": "Need-Time Ladder for Sovereign Bonds",
            "breakeven_horizon_hours": tau_b_hours,
            "breakeven_horizon_months": tau_b_hours / (24.0 * 30.5),
            "effective_liquid_pool_yield_pct": liquid_yield * 100.0,
            "insight": f"Bonds amortize their {h2 * 100:.1f}% market haircut only for capital not needed for {tau_b_hours/24.0/30.5:.1f} months.",
        },
    }
