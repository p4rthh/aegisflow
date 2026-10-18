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
    """Multi-quantile + Mean forecaster using ensembled LightGBM with calibrated coverage."""

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.mean_models: list[lgb.Booster] = []
        self.q_models: Dict[str, list[lgb.Booster]] = {"q50": [], "q90": [], "q99": []}
        self.quantiles = [0.5, 0.9, 0.99]

    def fit(self, X_train: np.ndarray, y_train: np.ndarray) -> "HourlyQuantileModel":
        """Train ensembled quantile regressors and L2 mean regressor."""
        train_data = lgb.Dataset(X_train, label=y_train, free_raw_data=False)
        seeds = [self.random_state, self.random_state + 1984]

        # 1. Ensembled L2 mean regressor (maximizes R2, minimizes MAE)
        self.mean_models = []
        for s in seeds:
            mean_params = {
                "objective": "regression",
                "learning_rate": 0.03,
                "num_leaves": 40,
                "min_data_in_leaf": 15,
                "feature_fraction": 0.82,
                "bagging_fraction": 0.85,
                "bagging_freq": 1,
                "reg_alpha": 0.1,
                "reg_lambda": 1.2,
                "verbosity": -1,
                "seed": s,
                "num_threads": 4,
            }
            self.mean_models.append(lgb.train(mean_params, train_data, num_boost_round=150))

        # 2. Calibrated quantile specs (fine-tuned for minimal pinball loss & exact empirical coverage)
        calibrated_specs = {
            0.5: {"target_alpha": 0.504, "lr": 0.04, "leaves": 32, "rounds": 100, "lambda": 1.0},
            0.9: {"target_alpha": 0.910, "lr": 0.045, "leaves": 28, "rounds": 85, "lambda": 1.0},
            0.99: {"target_alpha": 0.992, "lr": 0.045, "leaves": 26, "rounds": 75, "lambda": 1.0},
        }

        for q in self.quantiles:
            spec = calibrated_specs[q]
            key = f"q{int(q*100)}"
            self.q_models[key] = []
            for s in seeds:
                params = {
                    "objective": "quantile",
                    "alpha": spec["target_alpha"],
                    "learning_rate": spec["lr"],
                    "num_leaves": spec["leaves"],
                    "min_data_in_leaf": 15,
                    "feature_fraction": 0.85,
                    "reg_lambda": spec["lambda"],
                    "verbosity": -1,
                    "seed": s,
                    "num_threads": 4,
                }
                self.q_models[key].append(lgb.train(params, train_data, num_boost_round=spec["rounds"]))

        return self

    def predict(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """Predict quantiles and mean, enforcing monotonicity q50 <= q90 <= q99."""
        # Mean ensemble average
        mean = np.mean([m.predict(X) for m in self.mean_models], axis=0)

        # Quantile ensemble averages
        q50 = np.mean([m.predict(X) for m in self.q_models["q50"]], axis=0)
        q90 = np.mean([m.predict(X) for m in self.q_models["q90"]], axis=0)
        q99 = np.mean([m.predict(X) for m in self.q_models["q99"]], axis=0)

        # Enforce monotone quantiles: q50 <= q90 <= q99
        q90 = np.maximum(q50, q90)
        q99 = np.maximum(q90, q99)

        return {
            "q50": q50,
            "q90": q90,
            "q99": q99,
            "mean": mean,
        }

