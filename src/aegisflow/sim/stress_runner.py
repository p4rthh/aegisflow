"""Stress Test Simulation Runner.

See PROJECT_ROADMAP.md §5.4 & Task 10.
Executes stressed market simulation without lookahead or retraining.
"""

from typing import Dict, Any, List, Optional
import json
from pathlib import Path
import pandas as pd
import numpy as np

from aegisflow.config import AppConfig, get_default_config
from aegisflow.data.loader import load_dataset
from aegisflow.data.stress import apply_stress_shocks
from aegisflow.strategies.aegisflow import AegisFlow
from aegisflow.strategies.baseline2_static import Baseline2Static
from aegisflow.strategies.baseline0_cash import Baseline0Cash
from aegisflow.strategies.baseline1_greedy import Baseline1Greedy
from aegisflow.sim.engine import run_simulation


def run_stress_test(
    shocks: Dict[str, Any],
    df: Optional[pd.DataFrame] = None,
    aum0: float = 3_000_000_000.0,
    strategy_ids: Optional[List[str]] = None,
    config: Optional[AppConfig] = None,
    stride: int = 24,
) -> Dict[str, Any]:
    """Execute comparative stress test on shocked data against unshocked baseline."""
    if df is None:
        df = load_dataset()
    if config is None:
        config = get_default_config()
    if strategy_ids is None:
        strategy_ids = ["aegisflow", "baseline2_static"]

    # 1. Apply shocks to dataset
    df_shocked = apply_stress_shocks(df, shocks)

    # 2. Strategy factory
    strat_map = {
        "aegisflow": lambda: AegisFlow(config=config),
        "baseline0_cash": lambda: Baseline0Cash(),
        "baseline1_greedy": lambda: Baseline1Greedy(),
        "baseline2_static": lambda: Baseline2Static(),
    }

    # 3. Load or compute unshocked baseline metrics for delta comparison
    baseline_json_path = Path("artifacts") / f"backtest_{int(aum0)}.json"
    unshocked_kpis = {}
    if baseline_json_path.exists():
        try:
            with open(baseline_json_path, "r") as f:
                unshocked_payload = json.load(f)
                cached_mode = unshocked_payload.get("risk_mode") or unshocked_payload.get("config", {}).get("risk_mode")
                cached_seed = unshocked_payload.get("seed") or unshocked_payload.get("config", {}).get("seed", 42)
                if (
                    cached_mode == config.risk_mode.value
                    and cached_seed == config.seed
                ):
                    unshocked_kpis = unshocked_payload.get("strategies", {})
        except Exception:
            unshocked_kpis = {}

    results: Dict[str, Any] = {}
    curves: Dict[str, List[float]] = {}
    events: List[Dict[str, Any]] = []

    n_hours = len(df_shocked)
    sample_indices = np.arange(0, n_hours, stride)
    if sample_indices[-1] != n_hours - 1:
        sample_indices = np.append(sample_indices, n_hours - 1)

    timestamps = [str(df_shocked["timestamp"].iloc[i]) for i in sample_indices]
    curves["timestamps"] = timestamps
    curves["stride"] = stride

    for sid in strategy_ids:
        if sid not in strat_map:
            continue
        strat = strat_map[sid]()
        sim_res = run_simulation(strat, df_shocked, aum0=aum0, config=config)
        kpis = sim_res.metrics

        # Calculate delta vs unshocked
        unshocked_strat = unshocked_kpis.get(sid)
        if not unshocked_strat:
            unshocked_sim = run_simulation(strat_map[sid](), df, aum0=aum0, config=config)
            unshocked_strat = unshocked_sim.metrics
            unshocked_kpis[sid] = unshocked_strat

        unshocked_pnl = unshocked_strat.get("net_pnl", kpis["net_pnl"])
        unshocked_hc = unshocked_strat.get("haircuts", {}).get("total", kpis["haircuts"]["total"])
        unshocked_od_int = unshocked_strat.get("overdraft", {}).get("interest_usd", kpis["overdraft"]["interest_usd"])
        unshocked_peak_od = unshocked_strat.get("overdraft", {}).get("peak_usd", kpis["overdraft"]["peak_usd"])

        delta = {
            "net_pnl": float(kpis["net_pnl"] - unshocked_pnl),
            "haircuts": float(kpis["haircuts"]["total"] - unshocked_hc),
            "od_interest": float(kpis["overdraft"]["interest_usd"] - unshocked_od_int),
            "peak_overdraft": float(kpis["overdraft"]["peak_usd"] - unshocked_peak_od),
        }

        results[sid] = {
            "kpis": kpis,
            "delta_vs_unshocked": delta,
        }

        econ_pnl = sim_res.ticks_df["econ_pnl"].to_numpy()
        curves[sid] = [float(econ_pnl[i]) for i in sample_indices]

        # Extract regime events if strategy is AegisFlow
        if hasattr(strat, "logger"):
            for rec in strat.logger.records:
                if "STRESS_ELEVATED" in rec.overlays or rec.type.value == "REGIME_CHANGE":
                    events.append({
                        "timestamp": rec.timestamp,
                        "type": "STRESS_ELEVATED",
                        "strategy": sid,
                        "details": rec.narrative,
                    })

    # Find worst night in shocked data
    worst_drain = 0.0
    worst_date = ""
    for idx, row in df_shocked.iterrows():
        if row["hour"] == 17 and idx + 15 <= n_hours:
            night_drain = float(-df_shocked["net_flow_usd"].iloc[idx : idx + 15].sum())
            if night_drain > worst_drain:
                worst_drain = night_drain
                worst_date = str(row["timestamp"]).split(" ")[0]

    worst_nights = [{
        "date": worst_date,
        "drain_usd": worst_drain,
        "aegisflow_overdraft_peak": results.get("aegisflow", {}).get("kpis", {}).get("overdraft", {}).get("peak_usd", 0.0),
    }]

    import uuid
    run_id = f"st_{uuid.uuid4().hex[:8]}"

    return {
        "run_id": run_id,
        "shocks_applied": shocks,
        "baseline_run_id": f"bt_{int(aum0)}_{config.risk_mode.value}",
        "results": results,
        "events": events[:20],  # sample key events
        "equity_curves": curves,
        "worst_nights": worst_nights,
    }
