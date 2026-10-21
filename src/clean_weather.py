
import json
from pathlib import Path

import pandas as pd
import requests


API_URL = "https://archive-api.open-meteo.com/v1/archive"

START_DATE = "2025-10-01"
END_DATE = "2025-10-07"

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
}

WEATHER_COLUMNS = [
    "temperature_max_c",
    "temperature_min_c",
    "precipitation_mm",
]


def fetch_city_weather(city, location):
    """Fetch historical weather and save the original JSON response."""

    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily": list(COLUMN_RENAME.keys())[1:],
        "timezone": location["timezone"],
    }

    response = requests.get(API_URL, params=params, timeout=30)

    print(f"{city}: HTTP {response.status_code}")
    response.raise_for_status()

    raw_json = response.json()

    if "daily" not in raw_json:
        raise ValueError(f"No daily weather data returned for {city}")

    # Save the original API response without transforming it.
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    raw_path = raw_dir / f"{city.lower().replace(' ', '_')}.json"

    with raw_path.open("w", encoding="utf-8") as file:
        json.dump(raw_json, file, indent=2)

    print(f"Saved raw response: {raw_path}")

    # Convert the daily JSON arrays into rows.
    daily_data = raw_json["daily"]
    city_df = pd.DataFrame(daily_data)

    city_df["city"] = city

    return city_df


def clean_weather_dataframe(df):
    """Standardize, validate, and clean a weather DataFrame."""

    cleaned = df.copy()

    # Standardize column names.
    cleaned = cleaned.rename(columns=COLUMN_RENAME)

    # Ensure the expected columns are present.
    required_columns = ["city", "date"] + WEATHER_COLUMNS
    missing_columns = set(required_columns) - set(cleaned.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    # Convert dates and measurements to consistent types.
    cleaned["date"] = pd.to_datetime(
        cleaned["date"], errors="coerce"
    )

    for column in WEATHER_COLUMNS:
        cleaned[column] = pd.to_numeric(
            cleaned[column], errors="coerce"
        )

    records_before = len(cleaned)

    # Check missing values before cleaning.
    print("\nMissing values before cleaning:")
    print(cleaned[required_columns].isna().sum())

    # A duplicate is defined as the same city and date.
    duplicates_before = cleaned.duplicated(
        subset=["city", "date"]
    ).sum()

    print(f"\nDuplicate city/date records: {duplicates_before}")

    # Remove rows without a city, valid date, or measurements.
    cleaned = cleaned.dropna(subset=required_columns)

    # Keep one record per city/date.
    cleaned = cleaned.drop_duplicates(
        subset=["city", "date"],
        keep="first",
    )

    # Sort for consistent downstream processing.
    cleaned = cleaned.sort_values(
        ["city", "date"]
    ).reset_index(drop=True)

    records_after = len(cleaned)

    print("\nMissing values after cleaning:")
    print(cleaned[required_columns].isna().sum())

    print("\nCleaning summary")
    print(f"Records before: {records_before}")
    print(f"Records after:  {records_after}")
    print(f"Records removed: {records_before - records_after}")

    return cleaned


def main():
    city_dataframes = []

    for city, location in CITIES.items():
        print(f"\nFetching weather for {city}...")

        city_df = fetch_city_weather(city, location)
        city_dataframes.append(city_df)

    # Combine all three cities into one DataFrame.
    raw_df = pd.concat(city_dataframes, ignore_index=True)

    print(f"\nTotal raw records: {len(raw_df)}")
    print("\nRaw DataFrame preview:")
    print(raw_df.head())

    # Clean the combined dataset.
    cleaned_df = clean_weather_dataframe(raw_df)

    # Save cleaned data separately from the raw JSON.
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "weather_cleaned.csv"
    cleaned_df.to_csv(output_path, index=False)

    print(f"\nCleaned CSV saved to: {output_path.resolve()}")
    print("\nCleaned DataFrame preview:")
    print(cleaned_df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
