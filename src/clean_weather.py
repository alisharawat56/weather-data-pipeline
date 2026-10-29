
"""Fetch, validate, clean, and save historical weather data."""

import json
import logging
from pathlib import Path

import pandas as pd
import requests

API_URL = "https://archive-api.open-meteo.com/v1/archive"
START_DATE = "2025-10-01"
END_DATE = "2025-10-07"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

CITIES = {
    "Champaign": {
        "latitude": 40.1164,
        "longitude": -88.2434,
        "timezone": "America/Chicago",
    },
    "Chicago": {
        "latitude": 41.8781,
        "longitude": -87.6298,
        "timezone": "America/Chicago",
    },
    "New York": {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "timezone": "America/New_York",
    },
}

COLUMN_RENAME = {
    "time": "date",
    "temperature_2m_max": "temperature_max_c",
    "temperature_2m_min": "temperature_min_c",
    "precipitation_sum": "precipitation_mm",
    "wind_speed_10m_max": "wind_speed_max_kmh",
}

WEATHER_COLUMNS = [
    "temperature_max_c",
    "temperature_min_c",
    "precipitation_mm",
    "wind_speed_max_kmh",
]

REQUIRED_API_FIELDS = list(COLUMN_RENAME)
OUTPUT_COLUMNS = ["city", "date", *WEATHER_COLUMNS]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def validate_response(payload, city):
    """Validate the structure and required fields of an API response."""
    if not isinstance(payload, dict):
        raise ValueError(f"{city}: API response must be a JSON object")

    daily = payload.get("daily")
    if not isinstance(daily, dict):
        raise ValueError(f"{city}: response has no valid 'daily' object")

    missing = set(REQUIRED_API_FIELDS) - set(daily)
    if missing:
        raise ValueError(
            f"{city}: missing required daily fields: {sorted(missing)}"
        )

    lengths = {}
    for field in REQUIRED_API_FIELDS:
        values = daily[field]
        if not isinstance(values, list):
            raise ValueError(f"{city}: daily field '{field}' must be a list")
        lengths[field] = len(values)

    if not lengths["time"]:
        raise ValueError(f"{city}: API returned no daily records")

    if len(set(lengths.values())) != 1:
        raise ValueError(
            f"{city}: daily fields have inconsistent lengths: {lengths}"
        )

    return payload


def fetch_data(city, location, session=None):
    """Fetch and validate historical weather data for one city."""
    client = session if session is not None else requests

    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily": [field for field in REQUIRED_API_FIELDS if field != "time"],
        "wind_speed_unit": "kmh",
        "timezone": location["timezone"],
    }

    response = client.get(API_URL, params=params, timeout=30)
    response.raise_for_status()

    try:
        payload = response.json()
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"{city}: API returned invalid JSON") from exc

    validate_response(payload, city)
    save_raw_response(city, payload)
    logger.info("Fetched and validated %s weather data", city)

    return payload


def save_raw_response(city, payload):
    """Save the validated API response without modifying it."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{city.lower().replace(' ', '_')}.json"
    path = RAW_DIR / filename

    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)

    logger.info("Saved raw response: %s", path)


def clean_records(payloads):
    """Convert validated city responses into standardized daily records."""
    frames = []

    for city, payload in payloads:
        validate_response(payload, city)
        frame = pd.DataFrame(payload["daily"]).rename(
            columns=COLUMN_RENAME
        )
        frame["city"] = city
        frames.append(frame[OUTPUT_COLUMNS])

    if not frames:
        raise ValueError("No weather responses were provided")

    cleaned = pd.concat(frames, ignore_index=True)

    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")

    for column in WEATHER_COLUMNS:
        cleaned[column] = pd.to_numeric(
            cleaned[column], errors="coerce"
        )

    before = len(cleaned)

    # Missing or malformed values cannot become usable measurements.
    cleaned = cleaned.dropna(subset=OUTPUT_COLUMNS)

    # Reject physically invalid precipitation/wind and reversed min/max.
    valid_measurements = (
        (cleaned["precipitation_mm"] >= 0)
        & (cleaned["wind_speed_max_kmh"] >= 0)
        & (
            cleaned["temperature_min_c"]
            <= cleaned["temperature_max_c"]
        )
    )
    cleaned = cleaned.loc[valid_measurements].copy()

    # A daily record is identified by city + date.
    cleaned = cleaned.drop_duplicates(
        subset=["city", "date"], keep="first"
    )

    start = pd.Timestamp(START_DATE)
    end = pd.Timestamp(END_DATE)
    cleaned = cleaned.loc[cleaned["date"].between(start, end)]

    cleaned = cleaned.sort_values(
        ["city", "date"]
    ).reset_index(drop=True)

    if cleaned.empty:
        raise ValueError("No valid weather records remain after cleaning")

    logger.info(
        "Cleaning complete: input=%d output=%d removed=%d",
        before,
        len(cleaned),
        before - len(cleaned),
    )

    return cleaned


# Keep the existing function name for compatibility with older tests/scripts.
def clean_weather_dataframe(df):
    """Clean an already flattened weather DataFrame."""
    required = set(OUTPUT_COLUMNS)
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    cleaned = df[OUTPUT_COLUMNS].copy()
    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")

    for column in WEATHER_COLUMNS:
        cleaned[column] = pd.to_numeric(
            cleaned[column], errors="coerce"
        )

    cleaned = cleaned.dropna(subset=OUTPUT_COLUMNS)
    cleaned = cleaned.loc[
        (cleaned["precipitation_mm"] >= 0)
        & (cleaned["wind_speed_max_kmh"] >= 0)
        & (
            cleaned["temperature_min_c"]
            <= cleaned["temperature_max_c"]
        )
    ]
    cleaned = cleaned.drop_duplicates(
        subset=["city", "date"], keep="first"
    )

    start = pd.Timestamp(START_DATE)
    end = pd.Timestamp(END_DATE)
    cleaned = cleaned.loc[cleaned["date"].between(start, end)]

    return cleaned.sort_values(
        ["city", "date"]
    ).reset_index(drop=True)


def save_cleaned_data(df):
    """Write standardized records to the processed CSV."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DIR / "weather_cleaned.csv"
    df.to_csv(output_path, index=False)
    logger.info("Saved %d cleaned records to %s", len(df), output_path)
    return output_path


def report_success(df, output_path):
    """Report a successful ingestion run."""
    logger.info(
        "Weather ingestion succeeded: %d records saved to %s",
        len(df),
        output_path,
    )


def report_failure(exc):
    """Report a failed ingestion run."""
    logger.exception("Weather ingestion failed: %s", exc)


def main():
    """Run the fetch, validate, clean, and save stages."""
    try:
        payloads = []
        for city, location in CITIES.items():
            logger.info("Fetching weather for %s", city)
            payloads.append((city, fetch_data(city, location)))

        cleaned = clean_records(payloads)
        output_path = save_cleaned_data(cleaned)
        report_success(cleaned, output_path)

    except Exception as exc:
        report_failure(exc)
        raise


if __name__ == "__main__":
    main()
