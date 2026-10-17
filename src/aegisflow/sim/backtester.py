"""Institutional Benchmark Suite and Comparative Backtester.

See PROJECT_ROADMAP.md §4.1, §4.4 & Task 9.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import pandas as pd
import numpy as np

from aegisflow.config import AppConfig, get_default_config
from aegisflow.data.loader import load_dataset
from aegisflow.strategies.baseline0_cash import Baseline0Cash
from aegisflow.strategies.baseline1_greedy import Baseline1Greedy
from aegisflow.strategies.baseline2_static import Baseline2Static
from aegisflow.strategies.aegisflow import AegisFlow
from aegisflow.sim.engine import run_simulation, SimulationResult


def run_comparative_backtest(
    df: Optional[pd.DataFrame] = None,
    aum0: float = 3_000_000_000.0,
    config: Optional[AppConfig] = None,
    stride: int = 24,
    save_artifacts: bool = True,
) -> Dict[str, Any]:
    """Execute all 4 core institutional strategies across the 8,760 hours.
    
    Produces comparative KPIs, downsampled equity curves, and alpha metrics.
    """
    if df is None:
        df = load_dataset()
    if config is None:
        config = get_default_config()

    config.aum0 = aum0
    run_id = f"bt_{int(aum0)}_{config.risk_mode.value}"

    strategies = {
        "baseline0_cash": Baseline0Cash(),
        "baseline1_greedy": Baseline1Greedy(),
        "baseline2_static": Baseline2Static(),
        "aegisflow": AegisFlow(config=config),
    }

    results: Dict[str, SimulationResult] = {}
    kpis: Dict[str, Any] = {}

    for s_id, strat in strategies.items():
        res = run_simulation(strat, df, aum0=aum0, config=config)
        results[s_id] = res
        kpis[s_id] = res.metrics

        if save_artifacts:
            art_dir = Path("artifacts")
            art_dir.mkdir(parents=True, exist_ok=True)
            res.ticks_df.to_parquet(art_dir / f"ticks_{s_id}.parquet", index=False)

    # Downsample timestamps and economic equity curves
    n_hours = len(df)
    sample_indices = np.arange(0, n_hours, stride)
    if sample_indices[-1] != n_hours - 1:
        sample_indices = np.append(sample_indices, n_hours - 1)

    timestamps = [str(df["timestamp"].iloc[i]) for i in sample_indices]
    equity_curves: Dict[str, List[float]] = {
        "stride": stride,
        "timestamps": timestamps,
    }
    for s_id, res in results.items():
        econ_pnl = res.ticks_df["econ_pnl"].to_numpy()
        equity_curves[s_id] = [float(econ_pnl[i]) for i in sample_indices]

    af_pnl = kpis["aegisflow"]["net_pnl"]
    alpha_vs = {
        "baseline0_cash": float(af_pnl - kpis["baseline0_cash"]["net_pnl"]),
        "baseline1_greedy": float(af_pnl - kpis["baseline1_greedy"]["net_pnl"]),
        "baseline2_static": float(af_pnl - kpis["baseline2_static"]["net_pnl"]),
    }

    comparison_payload = {
        "run_id": run_id,
        "aum0": float(aum0),
        "risk_mode": config.risk_mode.value,
        "n_hours": n_hours,
        "strategies": kpis,
        "equity_curves": equity_curves,
        "alpha_vs": alpha_vs,
    }

    if save_artifacts:
        art_dir = Path("artifacts")
        out_file = art_dir / f"backtest_{int(aum0)}.json"
        with open(out_file, "w") as f:
            json.dump(comparison_payload, f, indent=2)

    return comparison_payload
