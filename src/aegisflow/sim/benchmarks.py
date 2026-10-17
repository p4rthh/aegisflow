"""AUM Sensitivity and Sub-$2.59B Demonstration.

See PROJECT_ROADMAP.md §4.1 & Task 9.
Demonstrates:
  1. Sensitivity across $3B, $5B, $10B AUM
  2. Sub-$2.59B structural liquidity drain inevitability
"""

from typing import Dict, Any, List, Optional
import json
from pathlib import Path
import pandas as pd

from aegisflow.config import AppConfig, get_default_config
from aegisflow.data.loader import load_dataset
from aegisflow.strategies.aegisflow import AegisFlow
from aegisflow.strategies.baseline0_cash import Baseline0Cash
from aegisflow.strategies.baseline2_static import Baseline2Static
from aegisflow.sim.engine import run_simulation


def run_aum_sensitivity(
    df: Optional[pd.DataFrame] = None,
    aum_levels: Optional[List[float]] = None,
    config: Optional[AppConfig] = None,
    save_artifacts: bool = True,
) -> Dict[str, Any]:
    """Run AUM sensitivity across multiple starting balances."""
    if df is None:
        df = load_dataset()
    if config is None:
        config = get_default_config()
    if aum_levels is None:
        aum_levels = [2_000_000_000.0, 3_000_000_000.0, 5_000_000_000.0, 10_000_000_000.0]

    sensitivity_results: Dict[str, Any] = {}

    for aum in aum_levels:
        key = f"aum_{int(aum/1e9)}B" if aum >= 1e9 else f"aum_{int(aum/1e6)}M"
        cfg = config.model_copy(deep=True)
        cfg.aum0 = aum

        af = AegisFlow(config=cfg)
        b0 = Baseline0Cash()
        b2 = Baseline2Static()

        res_af = run_simulation(af, df, aum0=aum, config=cfg)
        res_b0 = run_simulation(b0, df, aum0=aum, config=cfg)
        res_b2 = run_simulation(b2, df, aum0=aum, config=cfg)

        sensitivity_results[key] = {
            "aum0_usd": float(aum),
            "aegisflow": {
                "net_pnl": float(res_af.metrics["net_pnl"]),
                "net_apy_pct": float(res_af.metrics["net_apy_pct"]),
                "overdraft_hours": int(res_af.metrics["overdraft"]["hours"]),
                "overdraft_interest": float(res_af.metrics["overdraft"]["interest_usd"]),
                "haircuts_usd": float(res_af.metrics["haircuts"]["total"]),
            },
            "baseline0_cash": {
                "net_pnl": float(res_b0.metrics["net_pnl"]),
                "net_apy_pct": float(res_b0.metrics["net_apy_pct"]),
                "overdraft_hours": int(res_b0.metrics["overdraft"]["hours"]),
                "overdraft_interest": float(res_b0.metrics["overdraft"]["interest_usd"]),
            },
            "baseline2_static": {
                "net_pnl": float(res_b2.metrics["net_pnl"]),
                "net_apy_pct": float(res_b2.metrics["net_apy_pct"]),
                "overdraft_hours": int(res_b2.metrics["overdraft"]["hours"]),
                "haircuts_usd": float(res_b2.metrics["haircuts"]["total"]),
            },
        }

    if save_artifacts:
        art_dir = Path("artifacts")
        art_dir.mkdir(parents=True, exist_ok=True)
        with open(art_dir / "sensitivity.json", "w") as f:
            json.dump(sensitivity_results, f, indent=2)

    return sensitivity_results
