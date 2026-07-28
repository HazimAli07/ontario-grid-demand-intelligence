# Data sources and permitted use

## Primary dataset

This project uses the Independent Electricity System Operator (IESO) **Hourly Demand Report**:

- Public report directory: https://reports-public.ieso.ca/public/Demand/
- Data directory description: https://www.ieso.ca/power-data/data-directory
- Definitions: https://www.ieso.ca/power-data/monthly-market-report
- Website terms: https://www.ieso.ca/terms-of-use

The pipeline downloads the annual 2022–2025 reports and the current report. Each source file contains hourly market demand and Ontario demand. The project removes the report preamble, validates the schema, creates a timestamp, de-duplicates overlapping current and annual files, and records the data cutoff in a quality report.

## Attribution

Copyright © 2004–present Independent Electricity System Operator, all rights reserved.

The IESO source data is governed by the IESO website terms, not by this repository's MIT code licence. This independent portfolio project is not affiliated with or endorsed by the IESO. The forecasts are educational and must not be used for electricity-market participation or grid operations.

## Reproducibility

Raw and cleaned row-level snapshots are generated locally under `data/bronze/` and `data/silver/` and excluded from version control. Small derived Gold tables and model-evaluation outputs are included so the dashboard can be inspected without re-downloading the source reports.

