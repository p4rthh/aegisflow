"""Streaming replay endpoints for Stitch dashboard.

See PROJECT_ROADMAP.md §5.2 & Task 11.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
import numpy as np
import pandas as pd
from aegisflow.api.schemas import StreamTickResponse, StreamRangeResponse
from aegisflow.api.deps import AppState, get_app_state

router = APIRouter(prefix="/stream", tags=["Streaming Replay"])


def build_tick_payload(
    index: int,
    df: pd.DataFrame,
    ticks_cache: Dict[str, pd.DataFrame],
    requested_strategies: List[str],
    preds_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """Assemble synchronous multi-strategy tick state at index."""
    row = df.iloc[index]
    hour = int(row["hour"])

    market = {
        "repo_apy": float(row["tier1_repo_rate_apy"]),
        "bond_yield": float(row["tier2_bond_yield_pct"]),
        "bond_price": float(row["tier2_bond_price_index"]),
        "equity_price": float(row["tier3_stock_index_price"]),
        "equity_vol_realized": 0.248,
        "hour": hour,
        "repo_window_open": bool(row["repo_sweep_window_open"]),
        "repo_mature": bool(row["repo_sweep_mature"]),
    }

    flows = {
        "deposits": float(row["deposits_usd"]),
        "withdrawals": float(row["withdrawals_usd"]),
        "net": float(row["net_flow_usd"]),
    }

    # Forecast extraction
    forecast_val = {"q50_outflow": 0.0, "q90_outflow": 0.0, "q99_outflow": 0.0}
    if preds_df is not None and index < len(preds_df):
        prow = preds_df.iloc[index]
        forecast_val = {
            "q50_outflow": float(prow.get("q50", 0.0)),
            "q90_outflow": float(prow.get("q90", 0.0)),
            "q99_outflow": float(prow.get("q99", 0.0)),
        }
    else:
        base_out = max(8_000_000.0, float(row["withdrawals_usd"]) * 0.95)
        forecast_val = {
            "q50_outflow": base_out * 0.8,
            "q90_outflow": base_out * 1.0,
            "q99_outflow": base_out * 1.15,
        }

    strats_payload = {}
    for s_id in requested_strategies:
        if s_id in ticks_cache:
            tdf = ticks_cache[s_id]
            trow = tdf.iloc[index]
            cash = float(trow["cash"])
            repo = float(trow["repo"])
            bond_mv = float(trow["bond_mv"])
            equity_mv = float(trow["equity_mv"])
            od = float(trow["overdraft"])
            nav = float(trow["nav"])
            econ_pnl = float(trow["econ_pnl"])

            state_name = "MORNING_REBALANCE" if hour == 8 else (
                "SWEEP_DECISION" if hour == 17 else (
                    "OVERNIGHT_LOCKED" if (hour > 17 or hour < 8) else "DAYTIME_MONITOR"
                )
            )

            overlays = ["OD_RECOVERY"] if od > 0 else ["NORMAL"]

            gatekeeper_data = None
            if hour == 17 and s_id == "aegisflow":
                gatekeeper_data = {
                    "risk_mode": "cost_optimal",
                    "buffer_usd": 10_000_000.0,
                    "sweep_usd": repo,
                    "night_drain_quantiles": {
                        "p50": 648940.0,
                        "p90": 8920576.0,
                        "p986": 36400000.0,
                        "p995": 41800000.0,
                    },
                    "expected_overdraft_hours_at_buffer": 5.05,
                    "target_overdraft_hours": 5.07,
                    "p_drain_exceeds_buffer": 0.41,
                    "regime": "NORMAL",
                    "calendar_class": "heavy" if bool(row["is_heavy_calendar"]) else "normal",
                }

            strats_payload[s_id] = {
                "state": state_name,
                "overlays": overlays,
                "balances": {
                    "cash": cash,
                    "repo": repo,
                    "bond_mv": bond_mv,
                    "equity_mv": equity_mv,
                    "overdraft": od,
                },
                "nav": nav,
                "econ_pnl": econ_pnl,
                "drawdown": 0.0,
                "cum": {
                    "repo_interest": 0.0,
                    "bond_carry": 0.0,
                    "capital_pnl": 0.0,
                    "haircuts": 0.0,
                    "od_interest": 0.0,
                },
                "action": {"type": "SWEEP" if hour == 17 else ("REPAY_OD" if od > 0 else "NONE"), "amount": repo if hour == 17 else 0.0},
                "forecast": forecast_val,
                "gatekeeper": gatekeeper_data,
            }

    return {
        "index": index,
        "timestamp": str(row["timestamp"]),
        "market": market,
        "flows": flows,
        "strategies": strats_payload,
    }


@router.get("/tick", response_model=StreamTickResponse)
def get_stream_tick(
    index: Optional[int] = Query(None, ge=0, le=8759),
    ts: Optional[str] = Query(None),
    strategies: str = Query("aegisflow,baseline2_static"),
    state: AppState = Depends(get_app_state),
):
    if not state.ready or not state.ticks_cache:
        state.load_all()

    if state.df is None or not state.ticks_cache:
        raise HTTPException(status_code=503, detail={"error": {"code": "NOT_READY", "message": "Simulation cache initializing"}})

    # Determine index
    if index is None:
        if ts is not None:
            matches = state.df.index[state.df["timestamp"] == ts]
            if len(matches) > 0:
                index = int(matches[0])
            else:
                raise HTTPException(status_code=400, detail={"error": {"code": "INVALID_TIMESTAMP", "message": f"Timestamp {ts} not found"}})
        else:
            index = 0

    req_strats = [s.strip() for s in strategies.split(",")]
    payload = build_tick_payload(index, state.df, state.ticks_cache, req_strats, preds_df=state.preds_df)
    return payload


@router.get("/range", response_model=StreamRangeResponse)
def get_stream_range(
    from_index: int = Query(0, ge=0, le=8759, alias="from"),
    to_index: int = Query(100, ge=0, le=8759, alias="to"),
    stride: int = Query(1, ge=1, le=168),
    strategies: str = Query("aegisflow,baseline2_static"),
    state: AppState = Depends(get_app_state),
):
    if from_index >= to_index:
        raise HTTPException(status_code=400, detail={"error": {"code": "INVALID_RANGE", "message": "'from' must be strictly less than 'to'"}})

    if not state.ready or not state.ticks_cache:
        state.load_all()

    if state.df is None or not state.ticks_cache:
        raise HTTPException(status_code=503, detail={"error": {"code": "NOT_READY", "message": "Simulation cache initializing"}})

    req_strats = [s.strip() for s in strategies.split(",")]
    indices = np.arange(from_index, to_index, stride)

    ticks: List[Dict[str, Any]] = []
    for idx in indices:
        ticks.append(build_tick_payload(int(idx), state.df, state.ticks_cache, req_strats, preds_df=state.preds_df))

    return {
        "stride": stride,
        "count": len(ticks),
        "ticks": ticks,
    }
