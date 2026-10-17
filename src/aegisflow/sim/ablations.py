"""Ablation Studies Suite.

See PROJECT_ROADMAP.md §4.1 & Task 9.
Proves that alpha is structurally distributed across all quantitative components:
  1. AegisFlow (Full)
  2. AF - ladder (Repo-only, no bond investments)
  3. AF - waterfall (Fixed liquidity-rank order instead of cost-aware knapsack)
  4. B2+ (Static 20/30/30/20 with AegisFlow's cost-aware waterfall)
"""

from typing import Dict, Any, List, Optional
import json
from pathlib import Path
import pandas as pd

from aegisflow.config import AppConfig, get_default_config
from aegisflow.data.loader import load_dataset
from aegisflow.strategies.aegisflow import AegisFlow
from aegisflow.strategies.baseline2_static import Baseline2Static
from aegisflow.sim.engine import run_simulation


class AFNoLadder(AegisFlow):
    """AegisFlow variant with bond ladder disabled (repo only)."""
    def pre(self, t, row, state, ctx):
        # Prevent any bond purchases
        prev_burnin = self.ladder.burnin_days
        self.ladder.burnin_days = 999999
        res = super().pre(t, row, state, ctx)
        self.ladder.burnin_days = prev_burnin
        return res


class AFFixedWaterfall(AegisFlow):
    """AegisFlow variant using fixed liquidity-rank deficit resolution instead of cost-aware."""
    def resolve(self, t, shortfall, row, state, ctx):
        # Fixed order: Repo break -> Bond sell -> Equity sell -> OD
        plan = []
        rem = shortfall
        if state.repo_principal > 0.0 and rem > 0.0:
            gross = min(state.repo_principal, rem / (1.0 - 0.005))
            plan.append({"source": "T1_BREAK", "amount": gross})
            rem -= gross * (1.0 - 0.005)
        bond_price = float(row["tier2_bond_price_index"])
        bond_mv = state.bond_units * bond_price
        if bond_mv > 0.0 and rem > 0.0:
            gross = min(bond_mv, rem / (1.0 - 0.020))
            plan.append({"source": "T2_SELL", "amount": gross})
            rem -= gross * (1.0 - 0.020)
        stock_price = float(row["tier3_stock_index_price"])
        eq_mv = state.equity_units * stock_price
        if eq_mv > 0.0 and rem > 0.0:
            gross = min(eq_mv, rem / (1.0 - 0.150))
            plan.append({"source": "T3_SELL", "amount": gross})
            rem -= gross * (1.0 - 0.150)
        if rem > 0.0:
            plan.append({"source": "OD", "amount": rem})
        return plan


class Baseline2Plus(Baseline2Static):
    """Static 20/30/30/20 equipped with AegisFlow's cost-aware waterfall."""
    def __init__(self):
        super().__init__()
        self.af_waterfall = AegisFlow()

    def resolve(self, t, shortfall, row, state, ctx):
        return self.af_waterfall.resolve(t, shortfall, row, state, ctx)


def run_ablations(
    df: Optional[pd.DataFrame] = None,
    aum0: float = 3_000_000_000.0,
    config: Optional[AppConfig] = None,
    save_artifacts: bool = True,
) -> List[Dict[str, Any]]:
    """Run ablation suite and compute marginal component contributions."""
    if df is None:
        df = load_dataset()
    if config is None:
        config = get_default_config()

    variants = {
        "AegisFlow (Full Engine)": AegisFlow(config=config),
        "AF - No Bond Ladder (Repo Only)": AFNoLadder(config=config),
        "AF - Fixed Waterfall (Rank Order)": AFFixedWaterfall(config=config),
        "Baseline 2+ (Static with Cost Waterfall)": Baseline2Plus(),
    }

    full_pnl = None
    results: List[Dict[str, Any]] = []

    for name, strat in variants.items():
        res = run_simulation(strat, df, aum0=aum0, config=config)
        pnl = res.metrics["net_pnl"]
        if full_pnl is None:
            full_pnl = pnl

        row_data = {
            "variant": name,
            "net_pnl": float(pnl),
            "delta_vs_aegisflow": float(pnl - full_pnl),
            "haircuts_total": float(res.metrics["haircuts"]["total"]),
            "overdraft_interest": float(res.metrics["overdraft"]["interest_usd"]),
            "capital_efficiency_ratio": float(res.metrics["capital_efficiency_ratio"]),
        }
        results.append(row_data)

    if save_artifacts:
        art_dir = Path("artifacts")
        art_dir.mkdir(parents=True, exist_ok=True)
        with open(art_dir / "ablations.json", "w") as f:
            json.dump(results, f, indent=2)

    return results
