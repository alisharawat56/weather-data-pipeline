
import logging
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT_ROOT / "data" / "processed" / "weather_cleaned.csv"
LOG_PATH = PROJECT_ROOT / "logs" / "pipeline.log"

LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

load_dotenv(PROJECT_ROOT / ".env")


def get_engine():
    """Create a PostgreSQL connection engine from environment variables."""
    required = ["PGHOST", "PGDATABASE", "PGUSER", "PGPASSWORD"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise ValueError(f"Missing environment variables: {', '.join(missing)}")

    url = URL.create(
        "postgresql+psycopg",
        username=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5432")),
        database=os.environ["PGDATABASE"],
    )
    return create_engine(url, pool_pre_ping=True)


def load_cities(connection, dataframe):
    """Insert city records and return a city-name-to-ID mapping."""
    city_details = {
        "champaign": ("Champaign", "USA", 40.1164, -88.2434),
        "chicago": ("Chicago", "USA", 41.8781, -87.6298),
        "new york": ("New York", "USA", 40.7128, -74.0060),
    }

    names = (
        dataframe["city"].dropna().astype(str).str.strip().unique()
    )
    for name in names:
        details = city_details.get(name.lower())
        if details is None:
            raise ValueError(
                f"Coordinates not configured for city {name!r}. "
                "Add it to city_details before loading."
            )

        city_name, country, latitude, longitude = details
        connection.execute(
            text("""
                INSERT INTO cities (name, country, latitude, longitude)
                VALUES (:name, :country, :latitude, :longitude)
                ON CONFLICT (name, country) DO NOTHING
            """),
            {
                "name": city_name,
                "country": country,
                "latitude": latitude,
                "longitude": longitude,
            },
        )

    rows = connection.execute(
        text("""
            SELECT city_id, name
            FROM cities
            WHERE LOWER(name) = ANY(:names)
        """),
        {"names": [name.lower() for name in names]},
    ).mappings().all()

    return {row["name"].lower(): row["city_id"] for row in rows}



def load_observations(connection, dataframe, city_ids):
    """Insert cleaned daily observations without creating duplicates."""
    loaded = 0

    for _, row in dataframe.iterrows():
        city_name = str(row["city"]).strip().lower()
        city_id = city_ids.get(city_name)

        if city_id is None:
            raise ValueError(f"No database city ID found for {city_name!r}")

        observation_timestamp = pd.to_datetime(row["date"]).to_pydatetime()

        temp_max = row.get("temperature_max_c")
        temp_min = row.get("temperature_min_c")

        if pd.notna(temp_max) and pd.notna(temp_min):
            temperature = (float(temp_max) + float(temp_min)) / 2
        elif pd.notna(temp_max):
            temperature = float(temp_max)
        elif pd.notna(temp_min):
            temperature = float(temp_min)
        else:
            temperature = None

        precipitation = row.get("precipitation_mm")
        wind_speed = row.get("wind_speed_max_kmh")

        result = connection.execute(
            text("""
                INSERT INTO weather_observations (
                    city_id,
                    observation_timestamp,
                    temperature_c,
                    precipitation_mm,
                    wind_speed_kmh
                )
                VALUES (
                    :city_id,
                    :observation_timestamp,
                    :temperature_c,
                    :precipitation_mm,
                    :wind_speed_kmh
                )
                ON CONFLICT (city_id, observation_timestamp) DO NOTHING
                RETURNING observation_id
            """),
            {
                "city_id": city_id,
                "observation_timestamp": observation_timestamp,
                "temperature_c": temperature,
                "precipitation_mm": precipitation,
                "wind_speed_kmh": wind_speed,
            },
        )

        # This must be inside the loop.
        if result.scalar_one_or_none() is not None:
            loaded += 1

    return loaded


def verify_data(connection):
    """Run basic row-count, missing-data and average checks."""
    queries = {
        "City count": "SELECT COUNT(*) FROM cities",
        "Observation count": "SELECT COUNT(*) FROM weather_observations",
        "Observations missing temperature": """
            SELECT COUNT(*) FROM weather_observations
            WHERE temperature_c IS NULL
        """,
        "Observations missing precipitation": """
            SELECT COUNT(*) FROM weather_observations
            WHERE precipitation_mm IS NULL
        """,
        "Observations missing wind speed": """
            SELECT COUNT(*) FROM weather_observations
            WHERE wind_speed_kmh IS NULL
        """,
    }

    for label, query in queries.items():
        value = connection.execute(text(query)).scalar_one()
        logger.info("%s: %s", label, value)

    averages = connection.execute(text("""
        SELECT c.name,
               ROUND(AVG(w.temperature_c)::numeric, 2) AS avg_temp_c,
               ROUND(AVG(w.precipitation_mm)::numeric, 2) AS avg_precip_mm,
               ROUND(AVG(w.wind_speed_kmh)::numeric, 2) AS avg_wind_kmh
        FROM weather_observations w
        JOIN cities c ON c.city_id = w.city_id
        GROUP BY c.name
        ORDER BY c.name
    """)).mappings().all()

    for row in averages:
        logger.info("City averages: %s", dict(row))


def main():
    try:
        if not CSV_PATH.exists():
            raise FileNotFoundError(f"Cleaned CSV not found: {CSV_PATH}")

        dataframe = pd.read_csv(CSV_PATH)
        required_columns = {
            "city",
            "date",
            "temperature_max_c",
            "temperature_min_c",
            "precipitation_mm",
        }
        missing = required_columns - set(dataframe.columns)
        if missing:
            raise ValueError(
                f"CSV is missing expected columns: {sorted(missing)}. "
                f"Found: {list(dataframe.columns)}"
            )

        engine = get_engine()

        with engine.begin() as connection:
            connection.execute(text("SELECT 1"))
            logger.info("Connected to PostgreSQL successfully.")

            city_ids = load_cities(connection, dataframe)
            logger.info("City records processed successfully.")

            count = load_observations(connection, dataframe, city_ids)
            logger.info("Observation rows processed: %s", count)

            verify_data(connection)

        logger.info("Pipeline load completed successfully.")

    except Exception:
        logger.exception("Pipeline load failed.")
        raise


if __name__ == "__main__":
    main()
