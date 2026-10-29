
import pandas as pd
from sqlalchemy import text

from load_weather import get_engine


def main():
    csv_path = "data/processed/weather_cleaned.csv"
    df = pd.read_csv(csv_path)

    required = {"city", "date", "wind_speed_max_kmh"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(f"CSV is missing columns: {sorted(missing)}")

    engine = get_engine()

    update_sql = text("""
        UPDATE weather_observations AS w
        SET wind_speed_kmh = :wind_speed
        FROM cities AS c
        WHERE w.city_id = c.city_id
          AND LOWER(c.name) = LOWER(:city)
          AND w.observation_timestamp::date = :date
          AND w.wind_speed_kmh IS NULL
    """)

    updated = 0

    with engine.begin() as connection:
        for _, row in df.iterrows():
            result = connection.execute(
                update_sql,
                {
                    "city": row["city"],
                    "date": pd.to_datetime(row["date"]).date(),
                    "wind_speed": float(row["wind_speed_max_kmh"]),
                },
            )
            updated += result.rowcount

    print(f"Wind-speed values updated: {updated}")


if __name__ == "__main__":
    main()
