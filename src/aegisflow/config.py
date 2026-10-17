"""Configuration management using Pydantic v2.

See PROJECT_ROADMAP.md §1.2 & §1.3.
"""

from pathlib import Path
from typing import Optional, Dict, Any
import yaml
from pydantic import BaseModel, Field, model_validator
from aegisflow.types import RiskMode


class FrictionConfig(BaseModel):
    tier1_early_redemption_haircut: float = Field(0.005, description="0.5% Tier 1 early redemption fee")
    tier2_bond_liquidation_haircut: float = Field(0.020, description="2.0% Tier 2 bond liquidation haircut")
    tier3_stock_liquidation_haircut: float = Field(0.150, description="15.0% Tier 3 equity fire-sale haircut")
    emergency_overdraft_penalty_apr: float = Field(0.120, description="12.0% APR emergency overdraft penalty")


class BondConfig(BaseModel):
    duration: float = Field(1.92, description="Modified duration for 2Y sovereign bonds")
    zscore_veto: float = Field(2.0, description="Rate z-score purchase veto threshold")


class EquityConfig(BaseModel):
    w_cap: float = Field(0.15, description="Max 15% equity allocation")
    w_base: float = Field(0.10, description="Base target allocation")
    sigma_target: float = Field(0.10, description="Target portfolio equity volatility")
    gate_vol_max: float = Field(0.30, description="Realized vol cap (30%)")
    dd_gate: float = Field(-0.08, description="Max drawdown gate (-8% from 90d high)")
    breaker: float = Field(0.12, description="Circuit breaker threshold (-12% from peak)")
    freeze_days: int = Field(30, description="Freeze duration in days after breaker trips")
    permanent_horizon_years: float = Field(2.5, description="Horizon requirement for permanent capital")


class AppConfig(BaseModel):
    aum0: float = Field(3_000_000_000.0, description="Initial treasury capital in USD")
    seed: int = Field(42, description="Global random seed")
    risk_mode: RiskMode = Field(RiskMode.COST_OPTIMAL, description="Sizing mode: cost_optimal | guarded | conservative")
    overdraft_cap: Optional[float] = Field(None, description="Optional hard cap on overdraft facility in USD")
    guarded_cap: float = Field(25_000_000.0, description="Cap used for guarded mode constraint")
    epsilon: float = Field(0.005, description="Tail risk quantile probability (0.5% -> P99.5)")
    safety_margin: float = Field(0.10, description="Safety cushion on need-time ladder calculation")
    pool_days: int = Field(3, description="Days of reserve buffer required in liquid pool")
    bond_burnin_days: int = Field(35, description="Day threshold to activate bond ladder purchases")
    night_burnin_days: int = Field(14, description="Day threshold for night gatekeeper ML")
    night_prior_buffer: float = Field(50_000_000.0, description="Default conservative night buffer during burn-in")
    bond_momentum_veto_bps: float = Field(30.0, description="+30 bp 7d rate momentum purchase veto")
    purchase_cost_bps: float = Field(0.0, description="Purchase transaction cost in bps")
    frictions: FrictionConfig = Field(default_factory=FrictionConfig)
    bond: BondConfig = Field(default_factory=BondConfig)
    equity: EquityConfig = Field(default_factory=EquityConfig)

    @classmethod
    def load_yaml(cls, path: str | Path) -> "AppConfig":
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Config file not found: {p}")
        with open(p, "r") as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)


def get_default_config() -> AppConfig:
    """Load default config from configs/default.yaml or fall back to defaults."""
    default_path = Path(__file__).resolve().parents[2] / "configs" / "default.yaml"
    if default_path.exists():
        return AppConfig.load_yaml(default_path)
    return AppConfig()
