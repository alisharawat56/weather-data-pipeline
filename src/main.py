
import pandas as pd


def main():
    print("Welcome to the Weather Data Engineering Pipeline!")

    # Sample weather data for three cities
    weather_data = [
        {
            "city": "Champaign",
            "date": "2026-10-18",
            "temperature_max_c": 18.5,
            "temperature_min_c": 7.2,
            "precipitation_mm": 0.0,
        },
        {
            "city": "Chicago",
            "date": "2026-10-18",
            "temperature_max_c": 16.3,
            "temperature_min_c": 9.1,
            "precipitation_mm": 2.4,
        },
        {
            "city": "New York",
            "date": "2026-10-18",
            "temperature_max_c": 19.7,
            "temperature_min_c": 12.0,
            "precipitation_mm": 1.2,
        },
    ]

    # Convert the sample data into a Pandas DataFrame
    df = pd.DataFrame(weather_data)
    df["date"] = pd.to_datetime(df["date"])

    print("\nSample Weather Dataset:")
    print(df.to_string(index=False))

    print(f"\nTotal records: {len(df)}")
    print(f"Number of cities: {df['city'].nunique()}")


if __name__ == "__main__":
    main()
