from __future__ import annotations

import json

import joblib
import pandas as pd

from .config import ARTIFACTS_DIR, BRONZE_DIR, GOLD_DIR, SILVER_DIR, ensure_directories
from .data import build_quality_report, download_demand_data
from .features import FEATURE_COLUMNS, add_day_ahead_features, build_next_day_features
from .modeling import train_evaluate_forecaster


def _build_gold_tables(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    working = frame.copy()
    working["date"] = working["timestamp"].dt.date
    working["month"] = working["timestamp"].dt.to_period("M").astype(str)
    working["hour_of_day"] = working["timestamp"].dt.hour
    working["day_type"] = working["timestamp"].dt.dayofweek.map(
        lambda day: "Weekend" if day >= 5 else "Weekday"
    )

    daily = (
        working.groupby("date", as_index=False)
        .agg(
            average_demand_mw=("ontario_demand_mw", "mean"),
            peak_demand_mw=("ontario_demand_mw", "max"),
            minimum_demand_mw=("ontario_demand_mw", "min"),
            total_energy_gwh=("ontario_demand_mw", lambda values: values.sum() / 1000),
        )
        .sort_values("date")
    )
    peak_hours = working.loc[
        working.groupby("date")["ontario_demand_mw"].idxmax(),
        ["date", "hour_of_day"],
    ]
    daily = daily.merge(peak_hours, on="date", how="left")
    daily["load_factor"] = daily["average_demand_mw"] / daily["peak_demand_mw"]

    monthly = (
        working.groupby("month", as_index=False)
        .agg(
            average_demand_mw=("ontario_demand_mw", "mean"),
            peak_demand_mw=("ontario_demand_mw", "max"),
            total_energy_gwh=("ontario_demand_mw", lambda values: values.sum() / 1000),
        )
        .sort_values("month")
    )

    hourly_profile = (
        working.groupby(["day_type", "hour_of_day"], as_index=False)
        .agg(
            average_demand_mw=("ontario_demand_mw", "mean"),
            p90_demand_mw=("ontario_demand_mw", lambda values: values.quantile(0.90)),
        )
        .sort_values(["day_type", "hour_of_day"])
    )
    top_peaks = working.nlargest(25, "ontario_demand_mw")[
        ["timestamp", "ontario_demand_mw", "market_demand_mw"]
    ]
    return {
        "daily_demand": daily,
        "monthly_demand": monthly,
        "hourly_profile": hourly_profile,
        "top_peak_hours": top_peaks,
    }


def run_pipeline() -> dict[str, object]:
    ensure_directories()
    demand = download_demand_data()
    quality = build_quality_report(demand)
    demand.to_csv(BRONZE_DIR / "ieso_hourly_demand_snapshot.csv", index=False)

    silver = demand[
        [
            "timestamp",
            "date",
            "hour",
            "market_demand_mw",
            "ontario_demand_mw",
            "source_url",
        ]
    ].copy()
    silver.to_csv(SILVER_DIR / "hourly_demand_clean.csv", index=False)

    gold_tables = _build_gold_tables(silver)
    for name, table in gold_tables.items():
        table.to_csv(GOLD_DIR / f"{name}.csv", index=False)

    featured = add_day_ahead_features(silver)
    model, evaluation, metrics, importance, residual_bounds = train_evaluate_forecaster(
        featured
    )
    evaluation.to_csv(GOLD_DIR / "forecast_evaluation.csv", index=False)
    importance.to_csv(GOLD_DIR / "feature_importance.csv", index=False)

    future_features = build_next_day_features(silver)
    future_predictions = model.predict(future_features[FEATURE_COLUMNS])
    future = future_features[["timestamp"]].copy()
    future["forecast_demand_mw"] = future_predictions
    future["lower_90_mw"] = future_predictions + residual_bounds[0]
    future["upper_90_mw"] = future_predictions + residual_bounds[1]
    future.to_csv(GOLD_DIR / "next_24h_forecast.csv", index=False)

    joblib.dump(model, ARTIFACTS_DIR / "demand_forecaster.joblib")
    (ARTIFACTS_DIR / "feature_columns.json").write_text(
        json.dumps(FEATURE_COLUMNS, indent=2), encoding="utf-8"
    )
    (GOLD_DIR / "data_quality_report.json").write_text(
        json.dumps(quality, indent=2), encoding="utf-8"
    )
    (GOLD_DIR / "model_metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )

    return {
        "data_rows": quality["row_count"],
        "data_cutoff": quality["end_timestamp"],
        "test_mape_percent": round(metrics["model"]["mape_percent"], 3),
        "baseline_mape_percent": round(
            metrics["seasonal_naive_baseline"]["mape_percent"], 3
        ),
        "mae_improvement_percent": round(metrics["mae_improvement_percent"], 2),
        "next_forecast_start": future["timestamp"].min().isoformat(),
    }

