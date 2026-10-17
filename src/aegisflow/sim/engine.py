"""High-throughput simulation engine for treasury strategies.

See PROJECT_ROADMAP.md §4.1, §4.3 & Task 3.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from aegisflow.config import AppConfig, get_default_config
from aegisflow.ledger.state import PortfolioState
from aegisflow.ledger.engine_step import execute_canonical_step
from aegisflow.ledger.metrics import compute_metrics
from aegisflow.strategies.base import BaseStrategy


class SimulationResult:
    """Encapsulates backtest outputs, time series arrays, and performance metrics."""

    def __init__(
        self,
        strategy_name: str,
        aum0: float,
        final_state: PortfolioState,
        metrics: Dict[str, Any],
        ticks_df: pd.DataFrame,
    ):
        self.strategy_name = strategy_name
        self.aum0 = aum0
        self.final_state = final_state
        self.metrics = metrics
        self.ticks_df = ticks_df

    def summary(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy_name,
            "aum0": self.aum0,
            "net_pnl": self.metrics["net_pnl"],
            "net_apy_pct": self.metrics["net_apy_pct"],
            "max_drawdown_usd": self.metrics["max_drawdown_usd"],
            "overdraft_hours": self.metrics["overdraft"]["hours"],
            "overdraft_interest": self.metrics["overdraft"]["interest_usd"],
            "haircuts_total": self.metrics["haircuts"]["total"],
            "capital_efficiency_ratio": self.metrics["capital_efficiency_ratio"],
        }


def run_simulation(
    strategy: BaseStrategy,
    df: pd.DataFrame,
    aum0: Optional[float] = None,
    config: Optional[AppConfig] = None,
    ctx: Optional[Any] = None,
) -> SimulationResult:
    """Run full walk-forward simulation of strategy over the DataFrame.
    
    Adheres strictly to the canonical event order (§1.3) and float tolerance.
    """
    if config is None:
        config = get_default_config()
    if aum0 is None:
        aum0 = config.aum0

    n_hours = len(df)
    state = PortfolioState(cash=aum0)
    strategy.init(df, aum0, config)

    # Preallocate output arrays for speed (<5s requirement)
    econ_pnl_arr = np.zeros(n_hours, dtype=np.float64)
    nav_arr = np.zeros(n_hours, dtype=np.float64)
    cash_arr = np.zeros(n_hours, dtype=np.float64)
    repo_arr = np.zeros(n_hours, dtype=np.float64)
    bond_mv_arr = np.zeros(n_hours, dtype=np.float64)
    equity_mv_arr = np.zeros(n_hours, dtype=np.float64)
    overdraft_arr = np.zeros(n_hours, dtype=np.float64)
    cum_net_flow_arr = np.zeros(n_hours, dtype=np.float64)
    deployed_arr = np.zeros(n_hours, dtype=np.float64)

    net_flows = df["net_flow_usd"].to_numpy(dtype=np.float64)
    bond_yields = df["tier2_bond_yield_pct"].to_numpy(dtype=np.float64)
    cum_flow = 0.0

    od_apr = config.frictions.emergency_overdraft_penalty_apr
    h1 = config.frictions.tier1_early_redemption_haircut
    h2 = config.frictions.tier2_bond_liquidation_haircut
    h3 = config.frictions.tier3_stock_liquidation_haircut

    for t in range(n_hours):
        row = df.iloc[t]
        tick = execute_canonical_step(
            t=t,
            row=row,
            state=state,
            strategy=strategy,
            ctx=ctx,
            cum_net_flow=cum_flow,
            aum0=aum0,
            od_apr=od_apr,
            h1=h1,
            h2=h2,
            h3=h3,
        )

        cum_flow = tick["cum_net_flow"]
        econ_pnl_arr[t] = tick["econ_pnl"]
        nav_arr[t] = tick["nav"]
        cash_arr[t] = tick["cash"]
        repo_arr[t] = tick["repo_principal"]
        bond_mv_arr[t] = tick["bond_mv"]
        equity_mv_arr[t] = tick["equity_mv"]
        overdraft_arr[t] = tick["overdraft"]
        cum_net_flow_arr[t] = cum_flow
        deployed_arr[t] = tick["repo_principal"] + tick["bond_mv"] + tick["equity_mv"]

    float_series = aum0 + cum_net_flow_arr
    metrics = compute_metrics(
        state=state,
        econ_pnl_series=econ_pnl_arr,
        nav_series=nav_arr,
        float_series=float_series,
        bond_yield_series=bond_yields,
        deployed_series=deployed_arr,
        aum0=aum0,
    )

    ticks_df = pd.DataFrame({
        "timestamp": df["timestamp"],
        "cash": cash_arr,
        "repo": repo_arr,
        "bond_mv": bond_mv_arr,
        "equity_mv": equity_mv_arr,
        "overdraft": overdraft_arr,
        "nav": nav_arr,
        "econ_pnl": econ_pnl_arr,
        "cum_net_flow": cum_net_flow_arr,
    })

    return SimulationResult(
        strategy_name=strategy.name,
        aum0=aum0,
        final_state=state,
        metrics=metrics,
        ticks_df=ticks_df,
    )
