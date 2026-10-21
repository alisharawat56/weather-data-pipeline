
import requests
import pandas as pd
from pathlib import Path


def main():
    # 1. API endpoint
    url = "https://archive-api.open-meteo.com/v1/archive"

    # 2. Request parameters
    params = {
        "latitude": 40.1164,
        "longitude": -88.2434,
        "start_date": "2025-10-01",
        "end_date": "2025-10-07",
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
        ],
        "timezone": "America/Chicago",
    }

    # 3. Send the HTTP request
    response = requests.get(url, params=params, timeout=30)

    print("HTTP Status Code:", response.status_code)
    response.raise_for_status()

    # 4. Inspect the JSON response
    data = response.json()

    print("\nResponse keys:", list(data.keys()))
    print("\nDaily weather JSON:")
    print(data["daily"])

    # 5. Extract the date and weather measurements
    daily = data["daily"]

    weather_data = {
        "date": daily["time"],
        "temperature_max_c": daily["temperature_2m_max"],
        "temperature_min_c": daily["temperature_2m_min"],
        "precipitation_mm": daily["precipitation_sum"],
    }

    # 6. Convert the extracted data into a DataFrame
    df = pd.DataFrame(weather_data)
    df["date"] = pd.to_datetime(df["date"])
    df.insert(0, "city", "Champaign")

    print("\nWeather DataFrame:")
    print(df.to_string(index=False))

    print(f"\nTotal records: {len(df)}")

    # 7. Save the DataFrame as a CSV file
    output_dir = Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "weather_champaign.csv"
    df.to_csv(output_file, index=False)

    print(f"\nCSV saved to: {output_file.resolve()}")


if __name__ == "__main__":
    main()
