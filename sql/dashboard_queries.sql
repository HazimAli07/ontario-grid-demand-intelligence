-- Databricks dashboard queries
-- Update the catalog/schema prefix if your notebook uses a different target.

-- 1. Executive KPI strip
SELECT
  ROUND(AVG(average_demand_mw), 0) AS avg_demand_mw,
  ROUND(MAX(peak_demand_mw), 0) AS peak_demand_mw,
  ROUND(AVG(load_factor), 3) AS avg_load_factor,
  ROUND(SUM(total_energy_gwh), 0) AS energy_served_gwh
FROM portfolio.ontario_grid_gold_daily
WHERE date >= date_sub(current_date(), 90);

-- 2. Daily operating trend
SELECT
  date,
  ROUND(average_demand_mw, 0) AS average_demand_mw,
  ROUND(peak_demand_mw, 0) AS peak_demand_mw,
  ROUND(load_factor, 3) AS load_factor
FROM portfolio.ontario_grid_gold_daily
ORDER BY date;

-- 3. Weekday versus weekend load shape
SELECT
  day_type,
  hour_of_day,
  ROUND(average_demand_mw, 0) AS average_demand_mw,
  ROUND(p90_demand_mw, 0) AS p90_demand_mw
FROM portfolio.ontario_grid_gold_hourly_profile
ORDER BY day_type, hour_of_day;

-- 4. Next 24-hour forecast
SELECT
  timestamp,
  ROUND(forecast_demand_mw, 0) AS forecast_demand_mw,
  ROUND(lower_90_mw, 0) AS lower_90_mw,
  ROUND(upper_90_mw, 0) AS upper_90_mw
FROM portfolio.ontario_grid_gold_forecast
ORDER BY timestamp;

-- 5. Highest historical demand hours
SELECT
  timestamp,
  ROUND(ontario_demand_mw, 0) AS ontario_demand_mw,
  ROUND(market_demand_mw, 0) AS market_demand_mw
FROM portfolio.ontario_grid_gold_peak_hours
ORDER BY ontario_demand_mw DESC
LIMIT 20;

