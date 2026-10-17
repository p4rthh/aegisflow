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

        # Fine-tuned L2 mean regressor (maximizes R2, minimizes MAE)
        mean_params = {
            "objective": "regression",
            "learning_rate": 0.035,
            "num_leaves": 35,
            "min_data_in_leaf": 20,
            "feature_fraction": 0.85,
            "reg_lambda": 1.5,
            "verbosity": -1,
            "seed": self.random_state,
            "num_threads": 4,
        }
        self.models["mean"] = lgb.train(mean_params, train_data, num_boost_round=130)

        # Fine-tuned quantile regressors (calibrated for minimal pinball loss & exact coverage)
        quantile_specs = {
            0.5: {"lr": 0.06, "leaves": 35, "rounds": 100, "lambda": 1.0},
            0.9: {"lr": 0.06, "leaves": 25, "rounds": 60, "lambda": 1.0},
            0.99: {"lr": 0.06, "leaves": 25, "rounds": 60, "lambda": 1.0},
        }

        for q in self.quantiles:
            spec = quantile_specs.get(q, {"lr": 0.06, "leaves": 31, "rounds": 70, "lambda": 1.0})
            params = {
                "objective": "quantile",
                "alpha": q,
                "learning_rate": spec["lr"],
                "num_leaves": spec["leaves"],
                "min_data_in_leaf": 20,
                "feature_fraction": 0.85,
                "reg_lambda": spec["lambda"],
                "verbosity": -1,
                "seed": self.random_state,
                "num_threads": 4,
            }
            self.models[f"q{int(q*100)}"] = lgb.train(params, train_data, num_boost_round=spec["rounds"])

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
