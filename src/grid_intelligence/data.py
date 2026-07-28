from __future__ import annotations

from io import StringIO
from typing import Iterable

import pandas as pd
import requests

from .config import CURRENT_REPORT_URL, HISTORICAL_YEARS, YEAR_REPORT_URL

EXPECTED_COLUMNS = {"date", "hour", "market_demand_mw", "ontario_demand_mw"}


def _extract_csv_payload(text: str) -> str:
    """Remove the IESO metadata preamble and return the CSV payload."""
    lines = text.splitlines()
    header_index = next(
        (index for index, line in enumerate(lines) if line.startswith("Date,Hour,")),
        None,
    )
    if header_index is None:
        raise ValueError("IESO report does not contain the expected Date,Hour header")
    return "\n".join(lines[header_index:])


def parse_ieso_report(text: str, source_url: str = "") -> pd.DataFrame:
    frame = pd.read_csv(StringIO(_extract_csv_payload(text)))
    frame = frame.rename(
        columns={
            "Date": "date",
            "Hour": "hour",
            "Market Demand": "market_demand_mw",
            "Ontario Demand": "ontario_demand_mw",
        }
    )
    missing = EXPECTED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing expected IESO columns: {sorted(missing)}")

    frame = frame[list(EXPECTED_COLUMNS)].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    for column in ("hour", "market_demand_mw", "ontario_demand_mw"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["source_url"] = source_url
    return frame


def download_report(url: str, timeout: int = 45) -> pd.DataFrame:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return parse_ieso_report(response.text, source_url=url)


def download_demand_data(
    years: Iterable[int] = HISTORICAL_YEARS,
    include_current: bool = True,
) -> pd.DataFrame:
    frames = [download_report(YEAR_REPORT_URL.format(year=year)) for year in years]
    if include_current:
        frames.append(download_report(CURRENT_REPORT_URL))

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.dropna(subset=["date", "hour", "ontario_demand_mw"])
    combined["hour"] = combined["hour"].astype(int)
    combined = combined[combined["hour"].between(1, 24)]
    combined["timestamp"] = combined["date"] + pd.to_timedelta(
        combined["hour"] - 1, unit="h"
    )
    combined = combined.sort_values(["timestamp", "source_url"])
    combined = combined.drop_duplicates(subset=["timestamp"], keep="last")
    return combined.sort_values("timestamp").reset_index(drop=True)


def build_quality_report(frame: pd.DataFrame) -> dict[str, object]:
    expected = pd.date_range(frame["timestamp"].min(), frame["timestamp"].max(), freq="h")
    observed = pd.DatetimeIndex(frame["timestamp"])
    missing_timestamps = expected.difference(observed)
    return {
        "row_count": int(len(frame)),
        "start_timestamp": frame["timestamp"].min().isoformat(),
        "end_timestamp": frame["timestamp"].max().isoformat(),
        "duplicate_timestamps": int(frame["timestamp"].duplicated().sum()),
        "missing_timestamps": int(len(missing_timestamps)),
        "missing_ontario_demand": int(frame["ontario_demand_mw"].isna().sum()),
        "missing_market_demand": int(frame["market_demand_mw"].isna().sum()),
        "minimum_ontario_demand_mw": float(frame["ontario_demand_mw"].min()),
        "maximum_ontario_demand_mw": float(frame["ontario_demand_mw"].max()),
    }

