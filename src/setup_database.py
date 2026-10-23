
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text


# Project root is the parent of src/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

required_variables = [
    "PGHOST",
    "PGPORT",
    "PGDATABASE",
    "PGUSER",
    "PGPASSWORD",
]

missing = [key for key in required_variables if not os.getenv(key)]

if missing:
    raise RuntimeError(
        f"Missing environment variables: {', '.join(missing)}"
    )


database_url = URL.create(
    drivername="postgresql+psycopg",
    username=os.environ["PGUSER"],
    password=os.environ["PGPASSWORD"],
    host=os.environ["PGHOST"],
    port=int(os.environ["PGPORT"]),
    database=os.environ["PGDATABASE"],
)

engine = create_engine(database_url)


def execute_sql_file(connection, filename):
    """Execute a project SQL file containing statements."""

    sql_path = PROJECT_ROOT / "sql" / filename
    sql_text = sql_path.read_text(encoding="utf-8")

    # These files contain simple SQL statements without
    # procedural blocks or semicolons inside string literals.
    statements = [
        statement.strip()
        for statement in sql_text.split(";")
        if statement.strip()
    ]

    for statement in statements:
        connection.exec_driver_sql(statement)


def main():
    with engine.begin() as connection:
        # Create tables and insert the sample data.
        execute_sql_file(connection, "schema.sql")
        execute_sql_file(connection, "sample_data.sql")

        # Verify counts and inspect the joined data.
        counts = connection.execute(
            text("""
                SELECT
                    (SELECT COUNT(*) FROM cities) AS city_count,
                    (SELECT COUNT(*)
                     FROM weather_observations) AS observation_count
            """)
        ).mappings().one()

        print(f"Cities: {counts['city_count']}")
        print(f"Observations: {counts['observation_count']}")

        result = connection.execute(
            text("""
                SELECT
                    c.name AS city,
                    c.country,
                    w.observation_timestamp,
                    w.temperature_c,
                    w.precipitation_mm,
                    w.wind_speed_kmh
                FROM weather_observations w
                JOIN cities c ON c.city_id = w.city_id
                ORDER BY c.name, w.observation_timestamp
            """)
        )

        df = pd.DataFrame(result.mappings().all())

        print("\nVerified weather observations:")
        print(df.to_string(index=False))


if __name__ == "__main__":
    try:
        main()
    finally:
        engine.dispose()
