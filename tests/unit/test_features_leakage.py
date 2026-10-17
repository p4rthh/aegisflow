"""Leakage test for feature engineering.

See PROJECT_ROADMAP.md Task 5:
'perturb all rows >= t in features and assert features at t unchanged'
"""

import pytest
import numpy as np
import pandas as pd
from aegisflow.data.loader import load_dataset
from aegisflow.data.features import build_feature_dataframe


def test_no_future_leakage():
    df = load_dataset()
    base_feats = build_feature_dataframe(df)

    # Test at multiple probe points
    probe_indices = [100, 500, 1000, 4000, 8000]

    for t in probe_indices:
        df_perturbed = df.copy()
        # Heavily perturb all future rows >= t
        df_perturbed.loc[t:, "deposits_usd"] *= 10.0
        df_perturbed.loc[t:, "withdrawals_usd"] *= 0.1
        df_perturbed.loc[t:, "net_flow_usd"] = (
            df_perturbed.loc[t:, "deposits_usd"] - df_perturbed.loc[t:, "withdrawals_usd"]
        )
        df_perturbed.loc[t:, "outflow"] = -df_perturbed.loc[t:, "net_flow_usd"]

        perturbed_feats = build_feature_dataframe(df_perturbed)

        # Features at row t must remain strictly identical
        base_row = base_feats.iloc[t].to_numpy(dtype=np.float64)
        perturbed_row = perturbed_feats.iloc[t].to_numpy(dtype=np.float64)

        # Allow no difference whatsoever
        assert np.allclose(base_row, perturbed_row, atol=1e-6), f"Leakage detected at row {t}!"
