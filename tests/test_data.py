from grid_intelligence.data import build_quality_report, parse_ieso_report


SAMPLE = """\\Hourly Demand Report,,,
\\Created at 2026-01-01 00:00:00,,,
\\For 2025,,,
Date,Hour,Market Demand,Ontario Demand
2025-01-01,1,17000,14000
2025-01-01,2,17100,14100
"""


def test_parse_ieso_report_removes_metadata_and_renames_columns():
    frame = parse_ieso_report(SAMPLE, "https://example.test/report.csv")
    assert len(frame) == 2
    assert frame.loc[0, "ontario_demand_mw"] == 14000
    assert frame.loc[0, "source_url"] == "https://example.test/report.csv"


def test_quality_report_detects_hourly_continuity():
    frame = parse_ieso_report(SAMPLE)
    frame["timestamp"] = frame["date"] + (frame["hour"] - 1).astype("timedelta64[h]")
    report = build_quality_report(frame)
    assert report["row_count"] == 2
    assert report["missing_timestamps"] == 0
    assert report["duplicate_timestamps"] == 0

