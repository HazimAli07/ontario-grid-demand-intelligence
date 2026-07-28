# Model card — Ontario demand forecaster

## Purpose

Estimate Ontario electricity demand for the next 24 hourly intervals as a portfolio demonstration of leakage-safe time-series feature engineering, chronological validation and operational analytics.

## Model

`HistGradientBoostingRegressor` from scikit-learn, using calendar signals and demand history available at least 24 hours before each prediction.

## Features

- Hour, day of week, month, day of year and weekend flag
- Cyclical hour and weekday encodings
- Demand lags at 24, 48 and 168 hours
- 24-hour and 168-hour rolling means shifted by 24 hours

## Evaluation

- Training, validation and test windows are chronological.
- The final 60 days are held out for testing.
- The preceding 60 days calibrate an empirical 90% prediction interval.
- Performance is compared with a seasonal-naive baseline using demand from the same hour one week earlier.

The latest exact metrics are stored in `data/gold/model_metrics.json` and displayed in the application. Metrics change when the current IESO report advances.

## Limitations

- Weather, holidays, outages, economic activity and demand-response events are not included.
- The interval reflects historical validation residuals and is not a formal probabilistic forecast.
- Source reports can be revised by the publisher.
- The model is educational and is not suitable for operational grid decisions.

## Responsible use

Use the output to demonstrate analytics and machine-learning practice. Do not use it for market bidding, system planning, emergency operations or public claims about future grid reliability.

