"""Data loader and preprocessor for treasury dataset.

See PROJECT_ROADMAP.md §1.2, §1.3 & Task 1.
"""

from pathlib import Path
from typing import Tuple, Optional
import pandas as pd
import numpy as np

from aegisflow.config import FrictionConfig
from aegisflow.data.calendar import is_heavy_drain_calendar


PERCENTAGE_COLS = [
    "tier1_repo_rate_apy",
    "tier2_bond_yield_pct",
    "tier3_stock_volatility_pct",
    "tier1_early_redemption_haircut_pct",
    "tier2_bond_liquidation_haircut_pct",
    "tier3_stock_liquidation_haircut_pct",
    "emergency_overdraft_penalty_apr_pct",
]


def load_dataset(csv_path: Optional[str | Path] = None) -> pd.DataFrame:
    """Load the 8,760-hour treasury dataset and convert to canonical units.
    
    Conventions:
    - USD in float64
    - Percentages converted to decimal fractions (e.g. 4.292 -> 0.04292)
    - Booleans properly cast
    - Sign convention: outflow = -net_flow_usd
    - Calendar attributes added
    """
    if csv_path is None:
        # Search common paths
        candidates = [
            Path("data/raw/treasury_4tier_dataset.csv"),
            Path("treasury_4tier_dataset.csv"),
            Path(__file__).resolve().parents[3] / "treasury_4tier_dataset.csv",
            Path(__file__).resolve().parents[3] / "data" / "raw" / "treasury_4tier_dataset.csv",
        ]
        for c in candidates:
            if c.exists():
                csv_path = c
                break
        if csv_path is None:
            raise FileNotFoundError("Could not locate treasury_4tier_dataset.csv")

    df = pd.read_csv(csv_path)

    # Clean boolean columns
    for bool_col in ["repo_sweep_window_open", "repo_sweep_mature"]:
        if df[bool_col].dtype == object:
            df[bool_col] = df[bool_col].astype(str).str.strip().str.lower() == "true"
        else:
            df[bool_col] = df[bool_col].astype(bool)

    # Convert percentage columns to decimal fractions
    for col in PERCENTAGE_COLS:
        if col in df.columns:
            df[col] = df[col].astype(np.float64) / 100.0

    # Parse timestamps
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Sign convention: outflow is positive when money drains
    df["outflow"] = -df["net_flow_usd"]

    # Calendar features
    df["hour"] = df["timestamp"].dt.hour
    df["dow"] = df["timestamp"].dt.dayofweek
    df["dom"] = df["timestamp"].dt.day
    df["month"] = df["timestamp"].dt.month
    df["index"] = np.arange(len(df))
    df["is_heavy_calendar"] = df["timestamp"].apply(is_heavy_drain_calendar)

    return df


def extract_frictions(df: pd.DataFrame) -> Tuple[FrictionConfig, float]:
    """Extract constant frictions and bond duration from dataset."""
    frictions = FrictionConfig(
        tier1_early_redemption_haircut=float(df["tier1_early_redemption_haircut_pct"].iloc[0]),
        tier2_bond_liquidation_haircut=float(df["tier2_bond_liquidation_haircut_pct"].iloc[0]),
        tier3_stock_liquidation_haircut=float(df["tier3_stock_liquidation_haircut_pct"].iloc[0]),
        emergency_overdraft_penalty_apr=float(df["emergency_overdraft_penalty_apr_pct"].iloc[0]),
    )
    d_mod = float(df["tier2_bond_mod_duration"].iloc[0])
    return frictions, d_mod
