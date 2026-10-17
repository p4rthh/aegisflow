"""Data integrity validator for treasury dataset.

See PROJECT_ROADMAP.md §0.1 & Task 1.
"""

from typing import Dict, Any
import pandas as pd
import numpy as np


def validate_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate dataset integrity against institutional rules in §0.1.
    
    Raises AssertionError if any rule is violated.
    Returns audit summary dictionary.
    """
    # 1. Shape and missing values
    assert len(df) == 8760, f"Expected 8,760 rows, got {len(df)}"
    assert df.isnull().sum().sum() == 0, "Dataset contains null/NaN values"

    # 2. Monotonic hourly contiguous
    time_diffs = df["timestamp"].diff().iloc[1:]
    assert (time_diffs == pd.Timedelta(hours=1)).all(), "Timestamps are not strictly contiguous hourly"

    # 3. Sweep and maturity flags
    sweep_open_count = int(df["repo_sweep_window_open"].sum())
    sweep_mature_count = int(df["repo_sweep_mature"].sum())
    assert sweep_open_count == 365, f"Expected 365 repo sweep window open flags, got {sweep_open_count}"
    assert sweep_mature_count == 365, f"Expected 365 repo sweep mature flags, got {sweep_mature_count}"

    # Verify sweep hours strictly align
    assert (df[df["repo_sweep_window_open"]]["hour"] == 17).all(), "repo_sweep_window_open occurs outside hour 17"
    assert (df[df["repo_sweep_mature"]]["hour"] == 8).all(), "repo_sweep_mature occurs outside hour 8"

    # 4. Net flow identity: net_flow_usd == deposits_usd - withdrawals_usd
    flow_diff = np.abs(df["net_flow_usd"] - (df["deposits_usd"] - df["withdrawals_usd"]))
    max_diff = float(flow_diff.max())
    assert max_diff <= 0.02, f"Net flow identity violated: max diff ${max_diff:.4f}"

    # 5. Sign convention: outflow == -net_flow_usd
    assert np.allclose(df["outflow"], -df["net_flow_usd"]), "Outflow sign convention mismatch"

    # 6. Constant columns invariance
    for col in [
        "tier1_early_redemption_haircut_pct",
        "tier2_bond_liquidation_haircut_pct",
        "tier3_stock_liquidation_haircut_pct",
        "emergency_overdraft_penalty_apr_pct",
        "tier2_bond_mod_duration",
    ]:
        nunique = df[col].nunique()
        assert nunique == 1, f"Expected column {col} to be strictly constant, found {nunique} unique values"

    audit_summary = {
        "rows": len(df),
        "columns": list(df.columns),
        "mean_deposits_usd": float(df["deposits_usd"].mean()),
        "mean_withdrawals_usd": float(df["withdrawals_usd"].mean()),
        "mean_net_flow_usd": float(df["net_flow_usd"].mean()),
        "sum_net_flow_usd": float(df["net_flow_usd"].sum()),
        "sweep_open_count": sweep_open_count,
        "sweep_mature_count": sweep_mature_count,
        "first_timestamp": str(df["timestamp"].iloc[0]),
        "last_timestamp": str(df["timestamp"].iloc[-1]),
    }
    return audit_summary


if __name__ == "__main__":
    from aegisflow.data.loader import load_dataset
    df = load_dataset()
    summary = validate_dataset(df)
    print("=== AUDIT VALIDATION PASSED ===")
    for k, v in summary.items():
        if isinstance(v, float):
            print(f"  {k}: {v:,.2f}")
        else:
            print(f"  {k}: {v}")
