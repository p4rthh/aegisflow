"""Backtest comparison, ablations, and sensitivity endpoints.

See PROJECT_ROADMAP.md §5.3 & Task 11.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from aegisflow.api.schemas import BacktestRunRequest
from aegisflow.api.deps import AppState, get_app_state
from aegisflow.sim.backtester import run_comparative_backtest
from aegisflow.types import RiskMode

router = APIRouter(prefix="/backtest", tags=["Backtest & Alpha"])


@router.get("/compare")
def get_backtest_compare(
    aum0: float = Query(3_000_000_000.0, ge=1e8),
    risk_mode: RiskMode = Query(RiskMode.COST_OPTIMAL),
    state: AppState = Depends(get_app_state),
):
    """Retrieve full 4-strategy comparative performance, KPIs, and equity curves."""
    if state.backtest_data:
        cached_aum = state.backtest_data.get("aum0") or state.backtest_data.get("config", {}).get("aum0")
        cached_mode = state.backtest_data.get("risk_mode") or state.backtest_data.get("config", {}).get("risk_mode")
        if (cached_aum is None or abs(float(cached_aum) - aum0) < 1.0) and (
            cached_mode is None or cached_mode == risk_mode.value
        ):
            return state.backtest_data

    # Generate dynamically if not cached or parameters differ
    if state.df is not None:
        cfg = state.config.model_copy(deep=True)
        cfg.risk_mode = risk_mode
        cfg.aum0 = aum0
        return run_comparative_backtest(state.df, aum0=aum0, config=cfg, save_artifacts=False)
    raise HTTPException(status_code=503, detail={"error": {"code": "NOT_READY", "message": "Backtest data not available"}})


@router.get("/ablations")
def get_ablations(state: AppState = Depends(get_app_state)):
    """Retrieve ablation ladder isolating component alpha contributions."""
    if not state.ablations_data:
        raise HTTPException(status_code=503, detail={"error": {"code": "NOT_READY", "message": "Ablations data not available"}})
    return state.ablations_data


@router.get("/frontier")
def get_safety_frontier(state: AppState = Depends(get_app_state)):
    """Retrieve Price-of-Safety frontier points across tolerance and overdraft caps."""
    if not state.frontier_data:
        raise HTTPException(status_code=503, detail={"error": {"code": "NOT_READY", "message": "Frontier data not available"}})
    return state.frontier_data


@router.get("/sensitivity")
def get_aum_sensitivity(state: AppState = Depends(get_app_state)):
    """Retrieve AUM sensitivity across $2B, $3B, $5B, $10B starting capital."""
    if not state.sensitivity_data:
        raise HTTPException(status_code=503, detail={"error": {"code": "NOT_READY", "message": "Sensitivity data not available"}})
    return state.sensitivity_data


@router.post("/run")
def run_custom_backtest(
    body: BacktestRunRequest,
    state: AppState = Depends(get_app_state),
):
    """Execute synchronous custom backtest run (< 5s runtime)."""
    if state.df is None:
        raise HTTPException(status_code=503, detail={"error": {"code": "NOT_READY", "message": "Dataset not loaded"}})

    try:
        cfg = state.config.model_copy(deep=True)
        cfg.aum0 = body.aum0
        cfg.risk_mode = RiskMode(body.risk_mode)
        cfg.seed = body.seed

        res = run_comparative_backtest(state.df, aum0=body.aum0, config=cfg, save_artifacts=False)
        return {
            "run_id": res["run_id"],
            "status": "ready",
            "results": res,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": {"code": "BACKTEST_FAILED", "message": str(e)}})
