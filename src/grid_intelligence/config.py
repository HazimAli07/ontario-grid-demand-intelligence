from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

HISTORICAL_YEARS = (2022, 2023, 2024, 2025)
CURRENT_REPORT_URL = "https://reports-public.ieso.ca/public/Demand/PUB_Demand.csv"
YEAR_REPORT_URL = (
    "https://reports-public.ieso.ca/public/Demand/PUB_Demand_{year}.csv"
)
SOURCE_DIRECTORY_URL = "https://reports-public.ieso.ca/public/Demand/"
RANDOM_STATE = 42


def ensure_directories() -> None:
    for path in (BRONZE_DIR, SILVER_DIR, GOLD_DIR, ARTIFACTS_DIR):
        path.mkdir(parents=True, exist_ok=True)

