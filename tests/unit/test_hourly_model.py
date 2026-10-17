"""Unit tests for hourly quantile regression model.

See PROJECT_ROADMAP.md Task 5.
"""

import pytest
import numpy as np
import pandas as pd
from aegisflow.data.loader import load_dataset
from aegisflow.data.features import build_feature_dataframe
from aegisflow.forecast.hourly_model import HourlyQuantileModel, pinball_loss


def test_monotone_quantiles():
    df = load_dataset()
    X = build_feature_dataframe(df).iloc[:500].to_numpy(dtype=np.float32)
    y = df["outflow"].iloc[:500].to_numpy(dtype=np.float32)

    model = HourlyQuantileModel(random_state=42).fit(X, y)
    preds = model.predict(X)

    # Monotonicity test: q50 <= q90 <= q99
    assert np.all(preds["q50"] <= preds["q90"] + 1e-4)
    assert np.all(preds["q90"] <= preds["q99"] + 1e-4)


def test_pinball_loss_ordering():
    # True values and predictions
    y_true = np.array([10.0, 20.0, 30.0])
    q_opt = np.array([10.0, 20.0, 30.0])
    q_bad = np.array([0.0, 0.0, 0.0])

    loss_opt = pinball_loss(y_true, q_opt, 0.5)
    loss_bad = pinball_loss(y_true, q_bad, 0.5)
    assert loss_opt < loss_bad
