import numpy as np
import pandas as pd

from grid_intelligence.features import add_day_ahead_features, build_next_day_features


def history(rows: int = 240) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2025-01-01", periods=rows, freq="h"),
            "ontario_demand_mw": np.arange(rows, dtype=float) + 10000,
            "market_demand_mw": np.arange(rows, dtype=float) + 12000,
        }
    )


def test_day_ahead_lags_use_only_known_history():
    featured = add_day_ahead_features(history())
    assert featured.loc[100, "lag_24h"] == featured.loc[76, "ontario_demand_mw"]
    assert featured.loc[200, "lag_168h"] == featured.loc[32, "ontario_demand_mw"]


def test_next_day_features_are_complete_for_24_hours():
    future = build_next_day_features(history(), horizon=24)
    assert len(future) == 24
    assert future["lag_24h"].notna().all()
    assert future["rolling_mean_168h_safe"].notna().all()

