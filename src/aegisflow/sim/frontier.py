"""Price-of-Safety Frontier Grid Generator.

See PROJECT_ROADMAP.md §2.3.4 & Task 9.
Quantifies the exact tradeoff between risk guardrails and net realized PnL.
"""

from typing import List, Dict, Any, Optional
import json
from pathlib import Path
import pandas as pd

from aegisflow.config import AppConfig, get_default_config
from aegisflow.data.loader import load_dataset
from aegisflow.strategies.aegisflow import AegisFlow
from aegisflow.sim.engine import run_simulation
from aegisflow.types import RiskMode


def run_price_of_safety_frontier(
    df: Optional[pd.DataFrame] = None,
    aum0: float = 3_000_000_000.0,
    config: Optional[AppConfig] = None,
    save_artifacts: bool = True,
) -> List[Dict[str, Any]]:
    """Compute the multi-point frontier grid across safety tolerance epsilon and overdraft cap K."""
    if df is None:
        df = load_dataset()
    if config is None:
        config = get_default_config()

    # Define representative policy grid
    test_cases = [
        {"name": "Cost-Optimal (No Cap)", "mode": RiskMode.COST_OPTIMAL, "cap": None, "eps": 0.005},
        {"name": "Guarded ($50M Cap)", "mode": RiskMode.GUARDED, "cap": 50_000_000.0, "eps": 0.005},
        {"name": "Guarded ($25M Cap)", "mode": RiskMode.GUARDED, "cap": 25_000_000.0, "eps": 0.005},
        {"name": "Guarded ($10M Cap)", "mode": RiskMode.GUARDED, "cap": 10_000_000.0, "eps": 0.005},
        {"name": "Conservative (P99.5, Zero OD)", "mode": RiskMode.CONSERVATIVE, "cap": 0.0, "eps": 0.005},
        {"name": "Ultra-Conservative (P99.9)", "mode": RiskMode.CONSERVATIVE, "cap": 0.0, "eps": 0.001},
    ]

    frontier_points: List[Dict[str, Any]] = []

    for tc in test_cases:
        cfg = config.model_copy(deep=True)
        cfg.risk_mode = tc["mode"]
        cfg.guarded_cap = tc["cap"] or 0.0
        cfg.overdraft_cap = tc["cap"]
        cfg.epsilon = tc["eps"]

        af = AegisFlow(config=cfg)
        res = run_simulation(af, df, aum0=aum0, config=cfg)
        m = res.metrics

        frontier_points.append({
            "policy_name": tc["name"],
            "risk_mode": tc["mode"].value,
            "epsilon": tc["eps"],
            "overdraft_cap_usd": tc["cap"],
            "net_pnl": float(m["net_pnl"]),
            "net_apy_pct": float(m["net_apy_pct"]),
            "overdraft_hours": int(m["overdraft"]["hours"]),
            "peak_overdraft_usd": float(m["overdraft"]["peak_usd"]),
            "overdraft_interest_usd": float(m["overdraft"]["interest_usd"]),
            "haircuts_usd": float(m["haircuts"]["total"]),
        })

    if save_artifacts:
        art_dir = Path("artifacts")
        art_dir.mkdir(parents=True, exist_ok=True)
        with open(art_dir / "frontier.json", "w") as f:
            json.dump(frontier_points, f, indent=2)

    return frontier_points
