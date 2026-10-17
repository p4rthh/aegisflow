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
    risk_mode: str = Query("cost_optimal"),
    state: AppState = Depends(get_app_state),
):
    """Retrieve full 4-strategy comparative performance, KPIs, and equity curves."""
    if not state.backtest_data:
        # Generate dynamically if not cached
        if state.df is not None:
            cfg = state.config.model_copy(deep=True)
            cfg.risk_mode = RiskMode(risk_mode)
            cfg.aum0 = aum0
            return run_comparative_backtest(state.df, aum0=aum0, config=cfg)
        raise HTTPException(status_code=503, detail={"error": {"code": "NOT_READY", "message": "Backtest data not available"}})

    return state.backtest_data


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
