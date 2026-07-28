from __future__ import annotations

import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "hour",
    "day_of_week",
    "month",
    "day_of_year",
    "is_weekend",
    "hour_sin",
    "hour_cos",
    "week_sin",
    "week_cos",
    "lag_24h",
    "lag_48h",
    "lag_168h",
    "rolling_mean_24h_safe",
    "rolling_mean_168h_safe",
]


def add_day_ahead_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Create calendar and history-only features suitable for 24-hour forecasts."""
    result = frame.sort_values("timestamp").copy()
    timestamp = pd.to_datetime(result["timestamp"])
    series = result["ontario_demand_mw"].astype(float)

    result["hour"] = timestamp.dt.hour
    result["day_of_week"] = timestamp.dt.dayofweek
    result["month"] = timestamp.dt.month
    result["day_of_year"] = timestamp.dt.dayofyear
    result["is_weekend"] = (result["day_of_week"] >= 5).astype(int)
    result["hour_sin"] = np.sin(2 * np.pi * result["hour"] / 24)
    result["hour_cos"] = np.cos(2 * np.pi * result["hour"] / 24)
    result["week_sin"] = np.sin(2 * np.pi * result["day_of_week"] / 7)
    result["week_cos"] = np.cos(2 * np.pi * result["day_of_week"] / 7)
    result["lag_24h"] = series.shift(24)
    result["lag_48h"] = series.shift(48)
    result["lag_168h"] = series.shift(168)
    result["rolling_mean_24h_safe"] = series.shift(24).rolling(24).mean()
    result["rolling_mean_168h_safe"] = series.shift(24).rolling(168).mean()
    return result


def build_next_day_features(frame: pd.DataFrame, horizon: int = 24) -> pd.DataFrame:
    history = frame.sort_values("timestamp").copy()
    latest_ns = pd.to_datetime(history["timestamp"]).astype("int64").max()
    start = pd.Timestamp(latest_ns + 3_600_000_000_000, unit="ns")
    future = pd.DataFrame(
        {
            "timestamp": pd.date_range(start, periods=horizon, freq="h"),
            "ontario_demand_mw": np.nan,
            "market_demand_mw": np.nan,
        }
    )
    combined = pd.concat(
        [history[["timestamp", "ontario_demand_mw", "market_demand_mw"]], future],
        ignore_index=True,
    )
    featured = add_day_ahead_features(combined)
    return featured.tail(horizon).copy()
