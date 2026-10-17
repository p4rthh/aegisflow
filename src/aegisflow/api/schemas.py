"""Pydantic schemas for FastAPI endpoints.

See PROJECT_ROADMAP.md §5 & Task 11.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str
    version: str
    dataset_hours: int
    artifacts_ready: bool


class MarketTick(BaseModel):
    repo_apy: float
    bond_yield: float
    bond_price: float
    equity_price: float
    equity_vol_realized: float
    hour: int
    repo_window_open: bool
    repo_mature: bool


class FlowTick(BaseModel):
    deposits: float
    withdrawals: float
    net: float


class StrategyBalances(BaseModel):
    cash: float
    repo: float
    bond_mv: float
    equity_mv: float
    overdraft: float


class StrategyCumCosts(BaseModel):
    repo_interest: float
    bond_carry: float
    capital_pnl: float
    haircuts: float
    od_interest: float


class StrategyTickState(BaseModel):
    state: str
    overlays: List[str]
    balances: StrategyBalances
    nav: float
    econ_pnl: float
    drawdown: float
    cum: StrategyCumCosts
    action: Dict[str, Any]
    forecast: Dict[str, Any]
    gatekeeper: Optional[Dict[str, Any]] = None


class StreamTickResponse(BaseModel):
    index: int
    timestamp: str
    market: MarketTick
    flows: FlowTick
    strategies: Dict[str, StrategyTickState]


class StreamRangeResponse(BaseModel):
    stride: int
    count: int
    ticks: List[StreamTickResponse]


class StressShockRequest(BaseModel):
    withdrawal_multiplier: float = Field(1.0, ge=0.5, le=5.0)
    deposit_multiplier: float = Field(1.0, ge=0.5, le=2.0)
    window: Optional[Dict[str, str]] = None
    run_event: Optional[Dict[str, Any]] = None
    rate_shock_bps: float = Field(0.0, ge=-500.0, le=500.0)
    rate_shock_ramp_hours: int = Field(168, ge=1)
    rate_shock_start: Optional[str] = None
    equity_crash_pct: float = Field(0.0, ge=-60.0, le=0.0)
    equity_crash_start: Optional[str] = None
    equity_crash_hours: int = Field(240, ge=1)


class StressSimulationRequest(BaseModel):
    aum0: float = Field(3_000_000_000.0, ge=1e8)
    seed: int = 42
    strategies: List[str] = ["aegisflow", "baseline2_static"]
    shocks: StressShockRequest


class BacktestRunRequest(BaseModel):
    aum0: float = Field(3_000_000_000.0, ge=1e8)
    risk_mode: str = "cost_optimal"
    seed: int = 42


class DecisionLogQuery(BaseModel):
    strategy: Optional[str] = None
    from_index: Optional[int] = None
    to_index: Optional[int] = None
    action_type: Optional[str] = None
    limit: int = 100
    cursor: Optional[int] = None
