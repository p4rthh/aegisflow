"""LightGBM Hourly Quantile Regressor and Pinball Loss Evaluator.

See PROJECT_ROADMAP.md §2.1 & Task 5.
"""

from typing import Dict, Any, Tuple, Optional
import numpy as np
import lightgbm as lgb


def pinball_loss(y_true: np.ndarray, y_pred: np.ndarray, alpha: float) -> float:
    """Compute empirical pinball loss for quantile alpha.
    
    L_alpha(y, q) = max(alpha * (y - q), (alpha - 1) * (y - q))
    """
    err = y_true - y_pred
    return float(np.mean(np.maximum(alpha * err, (alpha - 1.0) * err)))


class HourlyQuantileModel:
    """Multi-quantile + Mean forecaster using LightGBM."""

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.models: Dict[str, lgb.Booster] = {}
        self.quantiles = [0.5, 0.9, 0.99]

    def fit(self, X_train: np.ndarray, y_train: np.ndarray) -> "HourlyQuantileModel":
        """Train quantile regressors and L2 mean regressor."""
        train_data = lgb.Dataset(X_train, label=y_train, free_raw_data=False)

        # Base hyperparams tuned for high speed & stable convergence
        base_params = {
            "learning_rate": 0.08,
            "num_leaves": 31,
            "min_data_in_leaf": 20,
            "verbosity": -1,
            "seed": self.random_state,
            "num_threads": 4,
        }

        # Train quantiles
        for q in self.quantiles:
            params = dict(base_params)
            params["objective"] = "quantile"
            params["alpha"] = q
            self.models[f"q{int(q*100)}"] = lgb.train(params, train_data, num_boost_round=60)

        # Train L2 mean model
        mean_params = dict(base_params)
        mean_params["objective"] = "regression"
        self.models["mean"] = lgb.train(mean_params, train_data, num_boost_round=60)

        return self

    def predict(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """Predict quantiles and mean, enforcing monotonicity q50 <= q90 <= q99."""
        q50 = self.models["q50"].predict(X)
        q90 = self.models["q90"].predict(X)
        q99 = self.models["q99"].predict(X)
        mean = self.models["mean"].predict(X)

        # Enforce monotone quantiles: q50 <= q90 <= q99
        q90 = np.maximum(q50, q90)
        q99 = np.maximum(q90, q99)

        return {
            "q50": q50,
            "q90": q90,
            "q99": q99,
            "mean": mean,
        }
