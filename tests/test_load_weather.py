
import pandas as pd
import pytest

from src.load_weather import load_cities, load_observations


def test_load_observations_rejects_unknown_city():
    df = pd.DataFrame([
        {
            "city": "Unknown City",
            "date": "2025-10-01",
            "temperature_max_c": 20.0,
            "temperature_min_c": 10.0,
            "precipitation_mm": 0.0,
            "wind_speed_max_kmh": 5.0,
        }
    ])

    with pytest.raises(ValueError, match="No database city ID"):
        load_observations(None, df, {})


def test_load_observations_counts_only_inserted_rows():
    class FakeResult:
        def __init__(self, inserted_id):
            self.inserted_id = inserted_id

        def scalar_one_or_none(self):
            return self.inserted_id

    class FakeConnection:
        def __init__(self):
            self.calls = 0

        def execute(self, statement, params):
            self.calls += 1
            # First insert succeeds; second simulates a conflict.
            return FakeResult(100 if self.calls == 1 else None)

    df = pd.DataFrame([
        {
            "city": "Champaign",
            "date": "2025-10-01",
            "temperature_max_c": 20.0,
            "temperature_min_c": 10.0,
            "precipitation_mm": 0.0,
            "wind_speed_max_kmh": 5.0,
        },
        {
            "city": "Champaign",
            "date": "2025-10-02",
            "temperature_max_c": 21.0,
            "temperature_min_c": 11.0,
            "precipitation_mm": 1.0,
            "wind_speed_max_kmh": 6.0,
        },
    ])

    connection = FakeConnection()
    inserted = load_observations(
        connection, df, {"champaign": 1}
    )

    assert inserted == 1
    assert connection.calls == 2


def test_load_cities_rejects_unconfigured_city():
    class FakeConnection:
        def execute(self, statement, params):
            raise AssertionError("Unknown cities should fail before SQL")

    df = pd.DataFrame({"city": ["Atlantis"]})

    with pytest.raises(ValueError, match="Coordinates not configured"):
        load_cities(FakeConnection(), df)
