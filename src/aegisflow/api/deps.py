"""Application state and cached artifact dependencies.

See PROJECT_ROADMAP.md §5 & Task 11.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import json
import pandas as pd
from aegisflow.data.loader import load_dataset
from aegisflow.config import AppConfig, get_default_config


class AppState:
    """Holds in-memory cache of dataset, simulation ticks, and backtest results."""

    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.config: AppConfig = get_default_config()
        self.backtest_data: Dict[str, Any] = {}
        self.ablations_data: List[Dict[str, Any]] = []
        self.frontier_data: List[Dict[str, Any]] = []
        self.sensitivity_data: Dict[str, Any] = []
        self.ticks_cache: Dict[str, pd.DataFrame] = {}
        self.presets: Dict[str, Any] = {}
        self.ready: bool = False

    def load_all(self):
        """Load dataset, config, presets, and cached artifacts into memory."""
        self.df = load_dataset()
        self.config = get_default_config()

        # Load presets
        presets_path = Path("configs/stress_presets.yaml")
        if presets_path.exists():
            import yaml
            with open(presets_path, "r") as f:
                self.presets = yaml.safe_load(f).get("presets", {})

        art_dir = Path("artifacts")
        # Backtest comparison
        bt_file = art_dir / "backtest_3000000000.json"
        if bt_file.exists():
            with open(bt_file, "r") as f:
                self.backtest_data = json.load(f)

        # Ablations
        abl_file = art_dir / "ablations.json"
        if abl_file.exists():
            with open(abl_file, "r") as f:
                self.ablations_data = json.load(f)

        # Frontier
        fr_file = art_dir / "frontier.json"
        if fr_file.exists():
            with open(fr_file, "r") as f:
                self.frontier_data = json.load(f)

        # Sensitivity
        sens_file = art_dir / "sensitivity.json"
        if sens_file.exists():
            with open(sens_file, "r") as f:
                self.sensitivity_data = json.load(f)

        # Ticks parquet
        for strat in ["baseline0_cash", "baseline1_greedy", "baseline2_static", "aegisflow"]:
            t_file = art_dir / f"ticks_{strat}.parquet"
            if t_file.exists():
                self.ticks_cache[strat] = pd.read_parquet(t_file)

        self.ready = True


# Global singleton instance
app_state = AppState()


def get_app_state() -> AppState:
    return app_state
