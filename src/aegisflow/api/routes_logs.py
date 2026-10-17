"""Audit trail and decision log endpoints.

See PROJECT_ROADMAP.md §5.5 & Task 11.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from aegisflow.api.deps import AppState, get_app_state
from aegisflow.strategies.aegisflow import AegisFlow
from aegisflow.sim.engine import run_simulation

router = APIRouter(prefix="/logs", tags=["Audit Log"])

# In-memory log cache from default run
_cached_records: Optional[List[Dict[str, Any]]] = None


def get_cached_records(state: AppState) -> List[Dict[str, Any]]:
    global _cached_records
    if _cached_records is None and state.df is not None:
        af = AegisFlow(config=state.config)
        run_simulation(af, state.df, aum0=state.config.aum0, config=state.config)
        _cached_records = af.logger.to_list()
    return _cached_records or []


@router.get("/decisions")
def get_decisions(
    strategy: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None, alias="type"),
    from_index: Optional[int] = Query(None, alias="from"),
    to_index: Optional[int] = Query(None, alias="to"),
    limit: int = Query(100, ge=1, le=500),
    cursor: Optional[int] = Query(None),
    state: AppState = Depends(get_app_state),
):
    """Query structured institutional audit logs with filtering and pagination."""
    all_recs = get_cached_records(state)

    filtered = all_recs
    if strategy:
        filtered = [r for r in filtered if r["strategy"] == strategy]
    if action_type:
        filtered = [r for r in filtered if r["type"] == action_type]
    if from_index is not None:
        filtered = [r for r in filtered if r["index"] >= from_index]
    if to_index is not None:
        filtered = [r for r in filtered if r["index"] <= to_index]

    start_pos = cursor or 0
    end_pos = start_pos + limit
    items = filtered[start_pos:end_pos]
    next_cursor = end_pos if end_pos < len(filtered) else None

    # Sanitize inf or nan in nested dicts for standard JSON compliance
    def sanitize_val(v):
        if isinstance(v, float):
            if v == float("inf"):
                return 1e18
            elif v == float("-inf"):
                return -1e18
        elif isinstance(v, dict):
            return {k: sanitize_val(val) for k, val in v.items()}
        elif isinstance(v, list):
            return [sanitize_val(val) for val in v]
        return v

    sanitized_items = [sanitize_val(item) for item in items]

    return {
        "total": len(filtered),
        "count": len(sanitized_items),
        "cursor": cursor,
        "next_cursor": next_cursor,
        "items": sanitized_items,
    }
