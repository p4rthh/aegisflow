"""AegisFlow: Autonomous Institutional Treasury & Liquidity Engine.

See PROJECT_ROADMAP.md §3.3, §3.4 & Task 8.
Composes Quantile Forecasting, Night Path Gatekeeper, Need-Time Ladder,
Regime Detectors, and Cost-Aware Knapsack Waterfall.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from aegisflow.constants import (
    REPO_SWEEP_HOUR,
    REPO_MATURE_HOUR,
    REPO_LOCK_HOURS,
    DEFAULT_TIER1_HAIRCUT,
    DEFAULT_TIER2_HAIRCUT,
    DEFAULT_TIER3_HAIRCUT,
    DEFAULT_OVERDRAFT_APR,
)
from aegisflow.config import AppConfig, get_default_config
from aegisflow.ledger.state import PortfolioState
from aegisflow.ledger.instruments import (
    sweep_repo,
    buy_bond,
    sell_bond,
    buy_equity,
    sell_equity,
    repay_overdraft,
)
from aegisflow.ledger.accounting import compute_nav
from aegisflow.strategies.base import BaseStrategy
from aegisflow.types import EngineState, OverlayState, ActionType, RiskMode, GatekeeperResult
from aegisflow.forecast.walkforward import run_walkforward_forecast
from aegisflow.forecast.night_paths import NightPathEngine
from aegisflow.forecast.conformal import ConformalCalibrator
from aegisflow.forecast.cure_time import CureTimeEstimator
from aegisflow.regime.flow_regime import FlowRegimeDetector
from aegisflow.regime.rate_regime import RateRegimeDetector
from aegisflow.regime.equity_regime import EquityRegimeDetector
from aegisflow.optimize.ladder import NeedTimeLadder
from aegisflow.optimize.waterfall import compute_source_costs, solve_greedy_waterfall
from aegisflow.optimize.repo_sizing import calculate_sweep_sizing
from aegisflow.audit.decision_log import DecisionLogger
from aegisflow.audit.narrative import generate_narrative


class AegisFlow(BaseStrategy):
    """Institutional Treasury Engine with Dynamic Quantile Waterfall & Regime Awareness."""

    def __init__(self, config: Optional[AppConfig] = None):
        super().__init__(name="aegisflow")
        self.config = config or get_default_config()

        # Engine state and components
        self.state_enum = EngineState.DAYTIME_MONITOR
        self.overlays: List[str] = [OverlayState.NORMAL.value]
        self.logger = DecisionLogger(run_id="aegisflow_live")

        # Subsystems
        self.night_engine = NightPathEngine(n_paths=2000, seed=self.config.seed)
        self.conformal = ConformalCalibrator(target_coverage=1.0 - self.config.epsilon)
        self.cure_estimator = CureTimeEstimator()
        self.flow_regime = FlowRegimeDetector()
        self.rate_regime = RateRegimeDetector(veto_momentum_bps=self.config.bond_momentum_veto_bps)
        self.equity_regime = EquityRegimeDetector()
        self.ladder = NeedTimeLadder(
            safety_margin=self.config.safety_margin,
            pool_days=self.config.pool_days,
            burnin_days=self.config.bond_burnin_days,
        )

        # Walk-forward forecast cache
        self.preds_df: Optional[pd.DataFrame] = None
        self.d_hat: float = -289_000.0  # Initialized near long-term mean
        self.current_buffer: float = 10_000_000.0
        self.last_gatekeeper_result: Optional[GatekeeperResult] = None
        self.recent_night_actuals: List[float] = []

    def init(self, df: pd.DataFrame, aum0: float, config: AppConfig) -> None:
        """Initialize models, precalculated forecasts, and historical state."""
        self.config = config
        self.preds_df, _ = run_walkforward_forecast(df, burnin_days=self.config.night_burnin_days)

    def pre(
        self,
        t: int,
        row: pd.Series,
        state: PortfolioState,
        ctx: Any,
    ) -> List[Dict[str, Any]]:
        """Pre-flow execution: rebalancing, buffer replenishment, and 17:00 repo sweep."""
        hour = int(row["hour"])
        day = t // 24
        bond_price = float(row["tier2_bond_price_index"])
        bond_yield = float(row["tier2_bond_yield_pct"])
        stock_price = float(row["tier3_stock_index_price"])
        repo_rate = float(row["tier1_repo_rate_apy"])

        # Determine engine primary state
        if hour == REPO_MATURE_HOUR:
            self.state_enum = EngineState.MORNING_REBALANCE
        elif hour == REPO_SWEEP_HOUR:
            self.state_enum = EngineState.SWEEP_DECISION
        elif hour > REPO_SWEEP_HOUR or hour < REPO_MATURE_HOUR:
            self.state_enum = EngineState.OVERNIGHT_LOCKED
        else:
            self.state_enum = EngineState.DAYTIME_MONITOR

        # Maintain overlays
        self.overlays = []
        if state.overdraft > 1e-9:
            self.overlays.append(OverlayState.OD_RECOVERY.value)
        if self.flow_regime.current_state == OverlayState.STRESS_ELEVATED:
            self.overlays.append(OverlayState.STRESS_ELEVATED.value)
        if not self.overlays:
            self.overlays.append(OverlayState.NORMAL.value)

        # 1. First priority: Repay any outstanding overdraft if cash exists
        if state.overdraft > 1e-9 and state.cash > 1e-9:
            repaid = repay_overdraft(state, state.cash)
            if repaid > 1000.0:
                self.logger.log(
                    timestamp=str(row["timestamp"]),
                    index=t,
                    strategy=self.name,
                    state=self.state_enum,
                    overlays=self.overlays,
                    action_type=ActionType.OVERDRAFT_REPAY,
                    amount_usd=repaid,
                    state_before={"cash": state.cash + repaid, "overdraft": state.overdraft + repaid},
                    state_after={"cash": state.cash, "overdraft": state.overdraft},
                    reason_codes=["OD_RECOVERY_PRIORITY"],
                    cost_table=[],
                    forecast={},
                    realized_cost_usd=0.0,
                    narrative=f"Repaid ${repaid/1e6:.2f}M outstanding overdraft.",
                )

        nav = compute_nav(state, bond_price, stock_price)
        free_cash = max(0.0, state.cash - state.overdraft)

        # 2. Morning Rebalance at 08:00
        if hour == REPO_MATURE_HOUR and day >= self.config.bond_burnin_days:
            # Need-Time Targets
            is_stress = OverlayState.STRESS_ELEVATED.value in self.overlays
            eq_eligible, eq_reason = self.equity_regime.is_eligible_for_entry(
                current_price=stock_price,
                nav=nav,
                need_2_5yr=self.ladder.compute_need_usd(self.config.equity.permanent_horizon_years * 8760, self.d_hat),
                is_stress_elevated=is_stress,
            )

            targets = self.ladder.calculate_targets(
                t=t,
                nav=nav,
                d_hat=self.d_hat,
                bond_yield=bond_yield,
                repo_rate=repo_rate,
                equity_eligible=eq_eligible,
                w_equity_cap=self.config.equity.w_cap,
            )

            pool_req = targets["pool_req"]
            bond_target = targets["bond_target"]
            current_bond_mv = state.bond_units * bond_price

            # Only refill from bonds if cash falls below a critical operational threshold (e.g. 1.5 days drain)
            pool_critical_floor = self.ladder.compute_need_usd(36.0, self.d_hat)
            if free_cash < pool_critical_floor and current_bond_mv > 0.0:
                deficit_usd = pool_req - free_cash
                gross_to_sell = min(current_bond_mv, deficit_usd / (1.0 - DEFAULT_TIER2_HAIRCUT))
                proceeds, fee = sell_bond(state, gross_to_sell, bond_price, haircut=DEFAULT_TIER2_HAIRCUT)
                self.logger.log(
                    timestamp=str(row["timestamp"]),
                    index=t,
                    strategy=self.name,
                    state=self.state_enum,
                    overlays=self.overlays,
                    action_type=ActionType.BOND_SELL,
                    amount_usd=gross_to_sell,
                    state_before={"cash": state.cash - proceeds, "bond_mv": current_bond_mv},
                    state_after={"cash": state.cash, "bond_mv": state.bond_units * bond_price},
                    reason_codes=["POOL_REFILL_0800"],
                    cost_table=[],
                    forecast={"pool_req": pool_req, "deficit_usd": deficit_usd},
                    realized_cost_usd=fee,
                    narrative=f"Liquidated ${gross_to_sell/1e6:.2f}M bonds to refill liquid buffer to ${pool_req/1e6:.2f}M.",
                )

            # Deploy surplus cash into bonds if below target and veto clear
            elif free_cash > pool_req and current_bond_mv < bond_target:
                bond_deficit = bond_target - current_bond_mv
                avail_deploy = free_cash - pool_req
                spend = min(bond_deficit, avail_deploy)

                is_vetoed, veto_reason = self.rate_regime.is_purchase_vetoed(bond_yield)
                if not is_vetoed and not is_stress and spend > 100_000.0:
                    bought = buy_bond(state, spend, bond_price, cost_bps=self.config.purchase_cost_bps)
                    self.logger.log(
                        timestamp=str(row["timestamp"]),
                        index=t,
                        strategy=self.name,
                        state=self.state_enum,
                        overlays=self.overlays,
                        action_type=ActionType.BOND_BUY,
                        amount_usd=bought,
                        state_before={"cash": state.cash + bought, "bond_mv": current_bond_mv},
                        state_after={"cash": state.cash, "bond_mv": state.bond_units * bond_price},
                        reason_codes=["NEED_TIME_LADDER_BUY"],
                        cost_table=[],
                        forecast={"bond_target": bond_target, "spend": spend},
                        realized_cost_usd=0.0,
                        narrative=f"Deployed ${bought/1e6:.2f}M into 2Y Sovereign Bonds towards target ${bond_target/1e6:.2f}M.",
                    )

        # 3. 17:00 Repo Sweep Gatekeeper
        if hour == REPO_SWEEP_HOUR:
            free_for_sweep = max(0.0, state.cash - state.overdraft)

            # Retrieve mean forecast for the 15-hour overnight window (rows t to t+14)
            if self.preds_df is not None and t + REPO_LOCK_HOURS <= len(self.preds_df):
                mean_path_15 = self.preds_df["mean"].iloc[t : t + REPO_LOCK_HOURS].to_numpy()
            else:
                mean_path_15 = np.full(REPO_LOCK_HOURS, 1_000_000.0)

            is_heavy = bool(row["is_heavy_calendar"])
            conformal_scale = self.conformal.current_kappa
            if OverlayState.STRESS_ELEVATED.value in self.overlays:
                conformal_scale *= 1.5

            sim_results = self.night_engine.simulate_night(
                mean_forecast_15=mean_path_15,
                is_heavy=is_heavy,
                conformal_scale=conformal_scale,
            )

            gatekeeper_res = calculate_sweep_sizing(
                free_cash=free_for_sweep,
                repo_rate_apy=repo_rate,
                peak_drains=sim_results["peak_drains"],
                cumulative_paths=sim_results["cumulative_paths"],
                quantiles=sim_results["quantiles"],
                risk_mode=self.config.risk_mode,
                od_apr=self.config.frictions.emergency_overdraft_penalty_apr,
                h1=self.config.frictions.tier1_early_redemption_haircut,
                guarded_cap=self.config.guarded_cap,
                epsilon=self.config.epsilon,
                regime=self.overlays[0],
                calendar_class="heavy" if is_heavy else "normal",
            )

            self.current_buffer = gatekeeper_res.buffer_usd
            self.last_gatekeeper_result = gatekeeper_res

            # Execute Sweep
            if gatekeeper_res.sweep_usd > 1000.0:
                swept = sweep_repo(state, gatekeeper_res.sweep_usd, repo_rate)
                reason_codes = [f"RULE_{self.config.risk_mode.value.upper()}"]
                if is_heavy:
                    reason_codes.append("CALENDAR_HEAVY_DAY")

                forecast_meta = {
                    "buffer_usd": gatekeeper_res.buffer_usd,
                    "sweep_usd": swept,
                    "night_p995_usd": gatekeeper_res.night_drain_quantiles.get("p995", 0.0),
                    "target_od_hours": gatekeeper_res.target_overdraft_hours,
                    "expected_od_hours": gatekeeper_res.expected_overdraft_hours_at_buffer,
                    "risk_mode": self.config.risk_mode.value,
                }

                narrative_txt = generate_narrative(
                    action_type="SWEEP",
                    amount_usd=swept,
                    state_before={"cash": state.cash + swept, "repo": 0.0},
                    state_after={"cash": state.cash, "repo": swept},
                    reason_codes=reason_codes,
                    forecast=forecast_meta,
                )

                self.logger.log(
                    timestamp=str(row["timestamp"]),
                    index=t,
                    strategy=self.name,
                    state=self.state_enum,
                    overlays=self.overlays,
                    action_type=ActionType.SWEEP,
                    amount_usd=swept,
                    state_before={"cash": state.cash + swept, "repo": 0.0},
                    state_after={"cash": state.cash, "repo": swept},
                    reason_codes=reason_codes,
                    cost_table=[],
                    forecast=forecast_meta,
                    realized_cost_usd=0.0,
                    narrative=narrative_txt,
                )

        return []

    def resolve(
        self,
        t: int,
        shortfall: float,
        row: pd.Series,
        state: PortfolioState,
        ctx: Any,
    ) -> List[Dict[str, Any]]:
        """Cost-aware fractional knapsack deficit resolution."""
        hour = int(row["hour"])
        bond_price = float(row["tier2_bond_price_index"])
        stock_price = float(row["tier3_stock_index_price"])

        # Dynamic cure-time estimator
        def cure_fn(x: float) -> float:
            return self.cure_estimator.estimate_cure_hours(
                need=x,
                hour=hour,
                pending_repo=state.repo_principal,
                expected_hourly_inflow=max(0.0, self.d_hat),
            )

        sources = compute_source_costs(
            need=shortfall,
            state=state,
            cure_time_fn=cure_fn,
            od_apr=self.config.frictions.emergency_overdraft_penalty_apr,
            h1=self.config.frictions.tier1_early_redemption_haircut,
            h2=self.config.frictions.tier2_bond_liquidation_haircut,
            h3=self.config.frictions.tier3_stock_liquidation_haircut,
            overdraft_cap=self.config.overdraft_cap,
            bond_price=bond_price,
            stock_price=stock_price,
        )

        plan, cost_table = solve_greedy_waterfall(
            need=shortfall,
            sources=sources,
            h1=self.config.frictions.tier1_early_redemption_haircut,
            h2=self.config.frictions.tier2_bond_liquidation_haircut,
            h3=self.config.frictions.tier3_stock_liquidation_haircut,
        )

        # Log deficit resolution decision
        if len(plan) > 0:
            top_source = plan[0]["source"]
            act_type = ActionType.OVERDRAFT_DRAW if top_source == "OD" else (
                ActionType.REPO_BREAK if top_source == "T1_BREAK" else (
                    ActionType.BOND_SELL if top_source == "T2_SELL" else ActionType.EQUITY_SELL
                )
            )
            self.logger.log(
                timestamp=str(row["timestamp"]),
                index=t,
                strategy=self.name,
                state=self.state_enum,
                overlays=self.overlays,
                action_type=act_type,
                amount_usd=shortfall,
                state_before={"cash": state.cash, "overdraft": state.overdraft},
                state_after={"cash": 0.0, "overdraft": state.overdraft + (shortfall if top_source == "OD" else 0.0)},
                reason_codes=["WATERFALL_DEFICIT_RESOLUTION"],
                cost_table=cost_table,
                forecast={"shortfall": shortfall, "cure_hours": cure_fn(shortfall)},
                realized_cost_usd=0.0,
                narrative=f"Waterfall resolved ${shortfall/1e6:.2f}M deficit using {top_source}.",
            )

        return plan

    def post(
        self,
        t: int,
        row: pd.Series,
        state: PortfolioState,
        ctx: Any,
    ) -> None:
        """Update rolling estimators and regime detectors with realized row t data."""
        actual_outflow = float(row["outflow"])
        stock_price = float(row["tier3_stock_index_price"])
        bond_yield = float(row["tier2_bond_yield_pct"])

        # Update detectors
        self.rate_regime.update(bond_yield)
        self.equity_regime.update(stock_price)

        # Update rolling d_hat with institutional conservative floor (never underestimate structural drain)
        net_flow = float(row["net_flow_usd"])
        self.d_hat = min(-250_000.0, 0.995 * self.d_hat + 0.005 * net_flow)

        # Update flow CUSUM
        if self.preds_df is not None and t < len(self.preds_df):
            q50 = float(self.preds_df["q50"].iloc[t])
            q90 = float(self.preds_df["q90"].iloc[t])
            self.flow_regime.update(actual_outflow, q50, q90)

        # Record overnight realization at 08:00
        hour = int(row["hour"])
        if hour == REPO_MATURE_HOUR and self.last_gatekeeper_result is not None:
            if len(self.recent_night_actuals) == REPO_LOCK_HOURS:
                realized_night_drain = float(np.max(-np.cumsum(self.recent_night_actuals)))
                p995 = self.last_gatekeeper_result.night_drain_quantiles.get("p995", 50e6)
                self.conformal.update(realized_night_drain, p995)
                self.night_engine.update_history(
                    np.array(self.recent_night_actuals),
                    is_heavy=bool(row["is_heavy_calendar"]),
                )
            self.recent_night_actuals = []
        elif hour >= REPO_SWEEP_HOUR or hour < REPO_MATURE_HOUR:
            self.recent_night_actuals.append(net_flow)
