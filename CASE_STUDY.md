# Case study — Ontario Grid Demand Intelligence

## Business question

How can public hourly electricity data be transformed into a reliable operating view of Ontario demand, with an auditable 24-hour forecast that improves on a simple weekly baseline?

## Approach

I built a reproducible ingestion pipeline for IESO Hourly Demand Reports and organized it into Bronze, Silver and Gold layers. The Silver layer standardizes timestamps, numerical demand fields and source lineage while removing report overlap. Gold marts expose daily load factors, peak hours, monthly energy and weekday/weekend demand profiles.

For forecasting, I used a gradient-boosted regression model with calendar signals and history-only features. Every lag or rolling feature is available at least 24 hours before the prediction. Training, validation and test windows are chronological, and the prediction interval is calibrated on validation residuals rather than the test set.

## Verified result

On a 1,417-hour holdout ending July 28, 2026, the model reached:

- 6.28% MAPE
- 1,127 MW MAE
- 0.755 R²
- 39.3% lower MAE than a same-hour-last-week baseline

The quality layer processed 40,056 hourly observations with no missing demand values and no duplicate timestamps after de-duplication. It explicitly surfaced one missing source hour instead of silently imputing it.

## Decision value

The application makes four questions easy to answer:

1. How are average and peak system requirements changing?
2. Which hours create the most operating pressure?
3. How does the weekday demand shape differ from weekends?
4. What demand range should be expected over the next 24 hours?

## What I would add next

- Environment and Climate Change Canada weather features
- Ontario holiday and demand-response indicators
- MLflow experiment tracking and model registry
- Scheduled Databricks Workflows with freshness alerts
- A formal probabilistic forecasting model and interval-coverage monitoring

