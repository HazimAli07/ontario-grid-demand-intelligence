from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .config import RANDOM_STATE
from .features import FEATURE_COLUMNS


def regression_metrics(actual: pd.Series, predicted: np.ndarray) -> dict[str, float]:
    actual_array = np.asarray(actual, dtype=float)
    predicted_array = np.asarray(predicted, dtype=float)
    return {
        "mae_mw": float(mean_absolute_error(actual_array, predicted_array)),
        "rmse_mw": float(np.sqrt(mean_squared_error(actual_array, predicted_array))),
        "mape_percent": float(
            np.mean(np.abs((actual_array - predicted_array) / actual_array)) * 100
        ),
        "r2": float(r2_score(actual_array, predicted_array)),
    }


def chronological_split(
    frame: pd.DataFrame,
    validation_days: int = 60,
    test_days: int = 60,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    usable = frame.dropna(subset=FEATURE_COLUMNS + ["ontario_demand_mw"]).copy()
    final_day = usable["timestamp"].max().normalize()
    test_start = final_day - pd.Timedelta(days=test_days - 1)
    validation_start = test_start - pd.Timedelta(days=validation_days)

    train = usable[usable["timestamp"] < validation_start]
    validation = usable[
        (usable["timestamp"] >= validation_start)
        & (usable["timestamp"] < test_start)
    ]
    test = usable[usable["timestamp"] >= test_start]
    if min(len(train), len(validation), len(test)) == 0:
        raise ValueError("Not enough history for chronological train/validation/test split")
    return train, validation, test


def new_model() -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        learning_rate=0.06,
        max_iter=260,
        max_leaf_nodes=31,
        min_samples_leaf=24,
        l2_regularization=1.0,
        random_state=RANDOM_STATE,
    )


def train_evaluate_forecaster(
    featured: pd.DataFrame,
) -> tuple[
    HistGradientBoostingRegressor,
    pd.DataFrame,
    dict[str, object],
    pd.DataFrame,
    tuple[float, float],
]:
    train, validation, test = chronological_split(featured)
    validation_model = new_model().fit(train[FEATURE_COLUMNS], train["ontario_demand_mw"])
    validation_predictions = validation_model.predict(validation[FEATURE_COLUMNS])
    validation_residuals = validation["ontario_demand_mw"].to_numpy() - validation_predictions
    residual_bounds = (
        float(np.quantile(validation_residuals, 0.05)),
        float(np.quantile(validation_residuals, 0.95)),
    )

    train_validation = pd.concat([train, validation], ignore_index=True)
    model = new_model().fit(
        train_validation[FEATURE_COLUMNS], train_validation["ontario_demand_mw"]
    )
    predictions = model.predict(test[FEATURE_COLUMNS])
    baseline = test["lag_168h"].to_numpy()

    evaluation = test[["timestamp", "ontario_demand_mw"]].copy()
    evaluation["predicted_demand_mw"] = predictions
    evaluation["baseline_demand_mw"] = baseline
    evaluation["lower_90_mw"] = predictions + residual_bounds[0]
    evaluation["upper_90_mw"] = predictions + residual_bounds[1]
    evaluation["absolute_error_mw"] = np.abs(
        evaluation["ontario_demand_mw"] - evaluation["predicted_demand_mw"]
    )

    model_metrics = regression_metrics(evaluation["ontario_demand_mw"], predictions)
    baseline_metrics = regression_metrics(evaluation["ontario_demand_mw"], baseline)
    metrics: dict[str, object] = {
        "model": model_metrics,
        "seasonal_naive_baseline": baseline_metrics,
        "mae_improvement_percent": float(
            (baseline_metrics["mae_mw"] - model_metrics["mae_mw"])
            / baseline_metrics["mae_mw"]
            * 100
        ),
        "train_rows": int(len(train)),
        "validation_rows": int(len(validation)),
        "test_rows": int(len(test)),
        "train_end": train["timestamp"].max().isoformat(),
        "validation_end": validation["timestamp"].max().isoformat(),
        "test_end": test["timestamp"].max().isoformat(),
        "prediction_interval": "Empirical 90% interval calibrated on validation residuals",
    }

    sample = test.tail(min(1200, len(test)))
    importance = permutation_importance(
        model,
        sample[FEATURE_COLUMNS],
        sample["ontario_demand_mw"],
        scoring="neg_mean_absolute_error",
        n_repeats=4,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    feature_importance = pd.DataFrame(
        {
            "feature": FEATURE_COLUMNS,
            "importance_mae": importance.importances_mean,
        }
    ).sort_values("importance_mae", ascending=False)
    return model, evaluation, metrics, feature_importance, residual_bounds

