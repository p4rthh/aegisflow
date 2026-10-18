"""Feature engineering for hourly net flow / outflow forecaster.

See PROJECT_ROADMAP.md §2.1 & Task 5.
Strict causality constraint: all features at row t are computed from rows <= t-1 ONLY!
"""

from typing import List, Tuple
import numpy as np
import pandas as pd


FEATURE_NAMES: List[str] = [
    # Cyclical time encodings
    "hour_sin", "hour_cos",
    "dow_sin", "dow_cos",
    "dom_sin", "dom_cos",
    "month_sin", "month_cos",
    # Calendar flags
    "is_payday",
    "is_post_payday",
    "is_fri",
    "is_sat",
    "is_month_end",
    "days_since_payday",
    "is_heavy_calendar",
    # Lags of outflow (-net_flow)
    "lag_1", "lag_2", "lag_3", "lag_6", "lag_12", "lag_24", "lag_48", "lag_168",
    # Rolling momentum (computed strictly on lagged series)
    "roll_mean_6h", "roll_std_6h",
    "roll_mean_24h", "roll_std_24h",
    "roll_mean_168h", "roll_std_168h",
    "ewma_outflow_6h",
    "flow_zscore_6h",
    # Component deposit & withdrawal flows (strictly lagged <= t-1)
    "lag_dep_1", "lag_dep_24",
    "lag_with_1", "lag_with_24",
    "roll_mean_dep_24h", "roll_mean_with_24h",
    # Flow velocity, acceleration, and seasonal differences
    "flow_diff_1", "flow_accel", "flow_diff_24", "flow_diff_168",
    "dep_with_ratio_24h",
    "ewma_outflow_24h",
    # Interaction & Volatility Envelopes
    "is_weekend",
    "payday_hour_sin", "payday_hour_cos",
    "weekend_hour_sin", "weekend_hour_cos",
    "roll_min_24h", "roll_max_24h", "roll_range_24h",
    "net_momentum_1",
]


def build_feature_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Construct strictly causal feature matrix for hourly forecasting.
    
    Target: outflow = -net_flow_usd.
    Features: derived strictly from information up to t-1.
    """
    feats = pd.DataFrame(index=df.index)

    # 1. Cyclical time features (known at time t)
    hour = df["hour"].values
    dow = df["dow"].values
    dom = df["dom"].values
    month = df["month"].values

    feats["hour_sin"] = np.sin(2.0 * np.pi * hour / 24.0)
    feats["hour_cos"] = np.cos(2.0 * np.pi * hour / 24.0)
    feats["dow_sin"] = np.sin(2.0 * np.pi * dow / 7.0)
    feats["dow_cos"] = np.cos(2.0 * np.pi * dow / 7.0)
    feats["dom_sin"] = np.sin(2.0 * np.pi * dom / 31.0)
    feats["dom_cos"] = np.cos(2.0 * np.pi * dom / 31.0)
    feats["month_sin"] = np.sin(2.0 * np.pi * month / 12.0)
    feats["month_cos"] = np.cos(2.0 * np.pi * month / 12.0)

    # 2. Calendar indicators
    feats["is_payday"] = np.isin(dom, [1, 15]).astype(np.float64)
    feats["is_post_payday"] = np.isin(dom, [2, 3, 16, 17]).astype(np.float64)
    feats["is_fri"] = (dow == 4).astype(np.float64)
    feats["is_sat"] = (dow == 5).astype(np.float64)
    feats["is_month_end"] = (dom >= 28).astype(np.float64)
    feats["is_heavy_calendar"] = df["is_heavy_calendar"].astype(np.float64)

    # Days since payday (1st or 15th)
    days_since_p = np.zeros(len(df), dtype=np.float64)
    for i, d in enumerate(dom):
        if d >= 15:
            days_since_p[i] = d - 15
        else:
            days_since_p[i] = d - 1
    feats["days_since_payday"] = days_since_p

    # 3. Lags of target variable: MUST use shift(1) to avoid leakage!
    # target is outflow = -net_flow_usd
    outflow_series = df["outflow"]
    lag1 = outflow_series.shift(1).bfill()

    feats["lag_1"] = lag1
    feats["lag_2"] = outflow_series.shift(2).bfill()
    feats["lag_3"] = outflow_series.shift(3).bfill()
    feats["lag_6"] = outflow_series.shift(6).bfill()
    feats["lag_12"] = outflow_series.shift(12).bfill()
    feats["lag_24"] = outflow_series.shift(24).bfill()
    feats["lag_48"] = outflow_series.shift(48).bfill()
    feats["lag_168"] = outflow_series.shift(168).bfill()

    # 4. Rolling momentum strictly on lagged values (shift 1 applied)
    # Using pandas rolling on lag1 guarantees only past rows <= t-1 are observed!
    feats["roll_mean_6h"] = lag1.rolling(6, min_periods=1).mean()
    feats["roll_std_6h"] = lag1.rolling(6, min_periods=1).std().fillna(0.0)

    feats["roll_mean_24h"] = lag1.rolling(24, min_periods=1).mean()
    feats["roll_std_24h"] = lag1.rolling(24, min_periods=1).std().fillna(0.0)

    feats["roll_mean_168h"] = lag1.rolling(168, min_periods=1).mean()
    feats["roll_std_168h"] = lag1.rolling(168, min_periods=1).std().fillna(0.0)

    feats["ewma_outflow_6h"] = lag1.ewm(alpha=0.3, min_periods=1).mean()

    # Z-score over 6 hours
    std6 = feats["roll_std_6h"].values
    mean6 = feats["roll_mean_6h"].values
    z6 = np.zeros_like(mean6)
    valid_mask = std6 > 1e-4
    z6[valid_mask] = (lag1.values[valid_mask] - mean6[valid_mask]) / std6[valid_mask]
    feats["flow_zscore_6h"] = np.clip(z6, -5.0, 5.0)

    # 5. Component deposit & withdrawal flows (strictly lagged <= t-1)
    dep_series = df["deposits_usd"] if "deposits_usd" in df else pd.Series(0.0, index=df.index)
    withd_series = df["withdrawals_usd"] if "withdrawals_usd" in df else pd.Series(0.0, index=df.index)

    lag_dep_1 = dep_series.shift(1).bfill()
    lag_dep_24 = dep_series.shift(24).bfill()
    lag_with_1 = withd_series.shift(1).bfill()
    lag_with_24 = withd_series.shift(24).bfill()

    feats["lag_dep_1"] = lag_dep_1
    feats["lag_dep_24"] = lag_dep_24
    feats["lag_with_1"] = lag_with_1
    feats["lag_with_24"] = lag_with_24

    feats["roll_mean_dep_24h"] = lag_dep_1.rolling(24, min_periods=1).mean()
    feats["roll_mean_with_24h"] = lag_with_1.rolling(24, min_periods=1).mean()

    # 6. Flow velocity, acceleration, and seasonal differences
    feats["flow_diff_1"] = feats["lag_1"] - feats["lag_2"]
    feats["flow_accel"] = (feats["lag_1"] - feats["lag_2"]) - (feats["lag_2"] - feats["lag_3"])
    feats["flow_diff_24"] = feats["lag_1"] - feats["lag_24"]
    feats["flow_diff_168"] = feats["lag_1"] - feats["lag_168"]

    dep_with_ratio = feats["roll_mean_dep_24h"] / (feats["roll_mean_with_24h"] + 1e-5)
    feats["dep_with_ratio_24h"] = np.clip(dep_with_ratio, 0.1, 10.0)
    feats["ewma_outflow_24h"] = lag1.ewm(span=24, min_periods=1).mean()

    # 7. Causal interaction terms & volatility envelope
    is_weekend = np.isin(dow, [5, 6]).astype(np.float64)
    feats["is_weekend"] = is_weekend
    feats["payday_hour_sin"] = feats["is_payday"] * feats["hour_sin"]
    feats["payday_hour_cos"] = feats["is_payday"] * feats["hour_cos"]
    feats["weekend_hour_sin"] = is_weekend * feats["hour_sin"]
    feats["weekend_hour_cos"] = is_weekend * feats["hour_cos"]

    roll_min_24 = lag1.rolling(24, min_periods=1).min()
    roll_max_24 = lag1.rolling(24, min_periods=1).max()
    feats["roll_min_24h"] = roll_min_24
    feats["roll_max_24h"] = roll_max_24
    feats["roll_range_24h"] = roll_max_24 - roll_min_24
    feats["net_momentum_1"] = lag_dep_1 - lag_with_1

    return feats[FEATURE_NAMES]

