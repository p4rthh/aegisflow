"""Stress-testing and Chaos Injection endpoints.

See PROJECT_ROADMAP.md §5.4 & Task 11.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from aegisflow.api.schemas import StressSimulationRequest
from aegisflow.api.deps import AppState, get_app_state
from aegisflow.sim.stress_runner import run_stress_test

router = APIRouter(prefix="/simulate", tags=["Stress Testing & Chaos"])


@router.get("/presets")
def get_stress_presets(state: AppState = Depends(get_app_state)):
    """Retrieve preconfigured institutional stress-test presets."""
    return {"presets": state.presets}


@router.post("/stress-test")
def execute_stress_test(
    body: StressSimulationRequest,
    state: AppState = Depends(get_app_state),
):
    """Execute dynamic chaos injection simulation on shocked data (< 3s runtime)."""
    if state.df is None:
        raise HTTPException(status_code=503, detail={"error": {"code": "NOT_READY", "message": "Dataset not loaded"}})

    try:
        shocks_dict = body.shocks.model_dump(exclude_none=True)
        cfg = state.config.model_copy(deep=True)
        cfg.aum0 = body.aum0
        cfg.seed = body.seed

        res = run_stress_test(
            shocks=shocks_dict,
            df=state.df,
            aum0=body.aum0,
            strategy_ids=body.strategies,
            config=cfg,
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=422, detail={"error": {"code": "BAD_SHOCK_PARAM", "message": str(e)}})
