import numpy as np
import pandas as pd

from grid_intelligence.modeling import regression_metrics


def test_regression_metrics_are_correct_for_perfect_predictions():
    actual = pd.Series([100.0, 200.0, 300.0])
    metrics = regression_metrics(actual, np.array([100.0, 200.0, 300.0]))
    assert metrics["mae_mw"] == 0
    assert metrics["rmse_mw"] == 0
    assert metrics["mape_percent"] == 0
    assert metrics["r2"] == 1

