"""Walk-forward expanding window training and prediction pipeline.

See PROJECT_ROADMAP.md §2.1 & Task 5.
"""

import hashlib
from pathlib import Path
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd

from aegisflow.data.features import build_feature_dataframe
from aegisflow.forecast.hourly_model import HourlyQuantileModel, pinball_loss


def get_walkforward_cache_path(
    cache_path: str | Path,
    df: pd.DataFrame,
    burnin_days: int,
    retrain_freq_hours: int,
) -> Path:
    """Compute content- and parameter-fingerprinted cache path to prevent collisions."""
    cache_file = Path(cache_path)
    n_rows = len(df)
    t0 = str(df["timestamp"].iloc[0]) if "timestamp" in df and len(df) > 0 else "0"
    t1 = str(df["timestamp"].iloc[-1]) if "timestamp" in df and len(df) > 0 else str(n_rows)

    # Content hash of model input flow columns
    col_bytes = b""
    for col in ["deposits_usd", "withdrawals_usd", "outflow"]:
        if col in df:
            col_bytes += df[col].to_numpy().tobytes()
    content_hash = hashlib.sha256(col_bytes).hexdigest()[:8] if col_bytes else "empty"

    sig = f"{n_rows}_{t0}_{t1}_{burnin_days}_{retrain_freq_hours}_{content_hash}"
    h = hashlib.sha256(sig.encode("utf-8")).hexdigest()[:8]

    if cache_file.name == "hourly_preds.parquet":
        return cache_file.parent / f"hourly_preds_{h}.parquet"
    if not cache_file.stem.endswith(h):
        return cache_file.parent / f"{cache_file.stem}_{h}{cache_file.suffix}"
    return cache_file


def run_walkforward_forecast(
    df: pd.DataFrame,
    burnin_days: int = 21,
    retrain_freq_hours: int = 168,
    cache_path: str | Path = "artifacts/hourly_preds.parquet",
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Execute expanding window walk-forward training.
    
    Returns (predictions_df, performance_report).
    """
    cache_file = get_walkforward_cache_path(cache_path, df, burnin_days, retrain_freq_hours)
    if cache_file.exists():
        preds_df = pd.read_parquet(cache_file)
        return preds_df, {}

    X = build_feature_dataframe(df).to_numpy(dtype=np.float32)
    y = df["outflow"].to_numpy(dtype=np.float32)
    n_hours = len(df)

    burnin_hours = burnin_days * 24

    pred_q50 = np.zeros(n_hours, dtype=np.float32)
    pred_q90 = np.zeros(n_hours, dtype=np.float32)
    pred_q99 = np.zeros(n_hours, dtype=np.float32)
    pred_mean = np.zeros(n_hours, dtype=np.float32)

    # 1. Burn-in period (days 0..21): use expanding empirical quantiles / seasonal naive
    for t in range(burnin_hours):
        if t < 24:
            # First day: use historical initial priors
            pred_q50[t] = 0.0
            pred_q90[t] = 5_000_000.0
            pred_q99[t] = 15_000_000.0
            pred_mean[t] = 0.0
        else:
            past = y[:t]
            pred_q50[t] = float(np.percentile(past, 50))
            pred_q90[t] = float(np.percentile(past, 90))
            pred_q99[t] = float(np.percentile(past, 99))
            pred_mean[t] = float(np.mean(past))

    # 2. Walk-forward training (retrain every 168 hours)
    current_model: HourlyQuantileModel | None = None
    last_train_t = -1

    for t in range(burnin_hours, n_hours):
        # Check if weekly retrain is due
        if current_model is None or (t - last_train_t) >= retrain_freq_hours:
            X_train = X[:t]
            y_train = y[:t]
            current_model = HourlyQuantileModel(random_state=42).fit(X_train, y_train)
            last_train_t = t

        preds = current_model.predict(X[t : t + 1])
        pred_q50[t] = preds["q50"][0]
        pred_q90[t] = preds["q90"][0]
        pred_q99[t] = preds["q99"][0]
        pred_mean[t] = preds["mean"][0]

    preds_df = pd.DataFrame({
        "timestamp": df["timestamp"],
        "actual_outflow": y,
        "q50": pred_q50,
        "q90": pred_q90,
        "q99": pred_q99,
        "mean": pred_mean,
    })

    # Save to parquet cache
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    preds_df.to_parquet(cache_file, index=False)

    # Evaluate post-burnin metrics
    eval_mask = np.arange(n_hours) >= burnin_hours
    y_eval = y[eval_mask]
    q50_eval = pred_q50[eval_mask]
    q90_eval = pred_q90[eval_mask]
    q99_eval = pred_q99[eval_mask]

    # Seasonal naive baseline: same-hour-last-week (lag 168)
    naive_pred = np.roll(y, 168)[eval_mask]

    report = {
        "pinball_loss_q50": pinball_loss(y_eval, q50_eval, 0.5),
        "pinball_loss_q90": pinball_loss(y_eval, q90_eval, 0.9),
        "pinball_loss_q99": pinball_loss(y_eval, q99_eval, 0.99),
        "pinball_loss_naive_q50": pinball_loss(y_eval, naive_pred, 0.5),
        "empirical_coverage_q50": float(np.mean(y_eval <= q50_eval)),
        "empirical_coverage_q90": float(np.mean(y_eval <= q90_eval)),
        "empirical_coverage_q99": float(np.mean(y_eval <= q99_eval)),
    }

    return preds_df, report
