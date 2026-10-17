"""Type definitions, enums, and foundational data structures.

See PROJECT_ROADMAP.md §1.2 & §3.3.
"""

from enum import Enum
from typing import NamedTuple, Optional, List, Dict, Any
from dataclasses import dataclass


class RiskMode(str, Enum):
    COST_OPTIMAL = "cost_optimal"
    GUARDED = "guarded"
    CONSERVATIVE = "conservative"


class EngineState(str, Enum):
    MORNING_REBALANCE = "MORNING_REBALANCE"  # 08:00
    DAYTIME_MONITOR = "DAYTIME_MONITOR"      # 09:00 - 16:00
    SWEEP_DECISION = "SWEEP_DECISION"        # 17:00
    OVERNIGHT_LOCKED = "OVERNIGHT_LOCKED"    # 18:00 - 07:00


class OverlayState(str, Enum):
    NORMAL = "NORMAL"
    STRESS_ELEVATED = "STRESS_ELEVATED"
    OD_RECOVERY = "OD_RECOVERY"


class ActionType(str, Enum):
    NONE = "NONE"
    SWEEP = "SWEEP"
    REPO_BREAK = "REPO_BREAK"
    BOND_BUY = "BOND_BUY"
    BOND_SELL = "BOND_SELL"
    EQUITY_BUY = "EQUITY_BUY"
    EQUITY_SELL = "EQUITY_SELL"
    OVERDRAFT_DRAW = "OVERDRAFT_DRAW"
    OVERDRAFT_REPAY = "OVERDRAFT_REPAY"
    REGIME_CHANGE = "REGIME_CHANGE"
    VETO = "VETO"
    NOOP_SAMPLE = "NOOP_SAMPLE"


class LiquiditySource(str, Enum):
    OD = "OD"
    T1_BREAK = "T1_BREAK"
    T2_SELL = "T2_SELL"
    T3_SELL = "T3_SELL"


@dataclass
class CostSource:
    source: LiquiditySource
    unit_cost: float
    capacity: float
    chosen: bool = False
    allocated: float = 0.0


@dataclass
class GatekeeperResult:
    risk_mode: RiskMode
    buffer_usd: float
    sweep_usd: float
    night_drain_quantiles: Dict[str, float]
    expected_overdraft_hours_at_buffer: float
    target_overdraft_hours: float
    p_drain_exceeds_buffer: float
    regime: str
    calendar_class: str


@dataclass
class DecisionRecord:
    id: str
    run_id: str
    timestamp: str
    index: int
    strategy: str
    state: EngineState
    overlays: List[str]
    type: ActionType
    amount_usd: float
    state_before: Dict[str, float]
    state_after: Dict[str, float]
    reason_codes: List[str]
    cost_table: List[Dict[str, Any]]
    forecast: Dict[str, Any]
    realized_cost_usd: float
    narrative: str
