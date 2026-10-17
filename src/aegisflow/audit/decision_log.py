"""Decision record logger and storage.

See PROJECT_ROADMAP.md §5.5, §5.6 & Task 8.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from aegisflow.types import DecisionRecord, ActionType, EngineState


class DecisionLogger:
    """In-memory append-only log of institutional decisions."""

    def __init__(self, run_id: str = "default_run"):
        self.run_id = run_id
        self.records: List[DecisionRecord] = []
        self._counter: int = 0

    def log(
        self,
        timestamp: str,
        index: int,
        strategy: str,
        state: EngineState,
        overlays: List[str],
        action_type: ActionType,
        amount_usd: float,
        state_before: Dict[str, float],
        state_after: Dict[str, float],
        reason_codes: List[str],
        cost_table: List[Dict[str, Any]],
        forecast: Dict[str, Any],
        realized_cost_usd: float,
        narrative: str,
    ) -> DecisionRecord:
        """Create, append, and return a DecisionRecord."""
        self._counter += 1
        rec = DecisionRecord(
            id=f"dec_{self._counter:06d}",
            run_id=self.run_id,
            timestamp=timestamp,
            index=index,
            strategy=strategy,
            state=state,
            overlays=overlays,
            type=action_type,
            amount_usd=amount_usd,
            state_before=state_before,
            state_after=state_after,
            reason_codes=reason_codes,
            cost_table=cost_table,
            forecast=forecast,
            realized_cost_usd=realized_cost_usd,
            narrative=narrative,
        )
        self.records.append(rec)
        return rec

    def to_list(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": r.id,
                "run_id": r.run_id,
                "timestamp": r.timestamp,
                "index": r.index,
                "strategy": r.strategy,
                "state": r.state.value if hasattr(r.state, "value") else str(r.state),
                "overlays": r.overlays,
                "type": r.type.value if hasattr(r.type, "value") else str(r.type),
                "amount_usd": r.amount_usd,
                "state_before": r.state_before,
                "state_after": r.state_after,
                "reason_codes": r.reason_codes,
                "cost_table": r.cost_table,
                "forecast": r.forecast,
                "realized_cost_usd": r.realized_cost_usd,
                "narrative": r.narrative,
            }
            for r in self.records
        ]
