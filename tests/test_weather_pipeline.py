
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT_ROOT / "data" / "processed" / "weather_cleaned.csv"

EXPECTED_COLUMNS = {
    "date",
    "temperature_max_c",
    "temperature_min_c",
    "precipitation_mm",
    "wind_speed_max_kmh",
    "city",
}

START_DATE = pd.Timestamp("2025-10-01")
END_DATE = pd.Timestamp("2025-10-07")


def load_weather_data():
    """Load the cleaned weather CSV for testing."""
    assert CSV_PATH.exists(), (
        f"Cleaned CSV not found: {CSV_PATH}. "
        "Run python src/clean_weather.py first."
    )
    return pd.read_csv(CSV_PATH)


def test_expected_columns():
    """Check that all expected columns exist."""
    df = load_weather_data()

    assert EXPECTED_COLUMNS.issubset(set(df.columns))


def test_unique_city_date_observations():
    """Ensure each city has no duplicate date records."""
    df = load_weather_data()

    assert not df.duplicated(subset=["city", "date"]).any()


def test_valid_date_range():
    """Ensure dates are valid and inside the configured range."""
    df = load_weather_data()

    dates = pd.to_datetime(df["date"], errors="coerce")

    assert dates.notna().all(), "Invalid or missing dates found."
    assert dates.between(START_DATE, END_DATE).all(), (
        "Dates found outside the configured date range."
    )
