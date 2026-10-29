
import pandas as pd
import pytest

from src.clean_weather import (
    clean_records,
    clean_weather_dataframe,
    fetch_data,
    validate_response,
)


def valid_payload():
    return {
        "daily": {
            "time": ["2025-10-01", "2025-10-02"],
            "temperature_2m_max": [18.0, 19.0],
            "temperature_2m_min": [8.0, 9.0],
            "precipitation_sum": [0.0, 2.5],
            "wind_speed_10m_max": [12.0, 14.0],
        }
    }


def test_validate_response_accepts_valid_payload():
    payload = valid_payload()
    assert validate_response(payload, "Champaign") is payload


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {},
        {"daily": None},
        {"daily": {"time": ["2025-10-01"]}},
    ],
)
def test_validate_response_rejects_invalid_or_missing_fields(payload):
    with pytest.raises(ValueError):
        validate_response(payload, "Champaign")


def test_validate_response_rejects_different_array_lengths():
    payload = valid_payload()
    payload["daily"]["precipitation_sum"] = [0.0]

    with pytest.raises(ValueError, match="inconsistent lengths"):
        validate_response(payload, "Champaign")


def test_fetch_data_rejects_http_error():
    class FakeResponse:
        def raise_for_status(self):
            raise RuntimeError("HTTP error")

    class FakeSession:
        def get(self, *args, **kwargs):
            return FakeResponse()

    with pytest.raises(RuntimeError, match="HTTP error"):
        fetch_data(
            "Champaign",
            {
                "latitude": 40.1164,
                "longitude": -88.2434,
                "timezone": "America/Chicago",
            },
            session=FakeSession(),
        )


def test_clean_records_keeps_zero_precipitation():
    cleaned = clean_records([("Champaign", valid_payload())])

    assert len(cleaned) == 2
    assert cleaned.loc[0, "precipitation_mm"] == 0.0


def test_clean_records_removes_duplicate_city_dates():
    payload = valid_payload()
    payload["daily"]["time"].append("2025-10-01")
    payload["daily"]["temperature_2m_max"].append(18.0)
    payload["daily"]["temperature_2m_min"].append(8.0)
    payload["daily"]["precipitation_sum"].append(0.0)
    payload["daily"]["wind_speed_10m_max"].append(12.0)

    cleaned = clean_records([("Champaign", payload)])

    assert not cleaned.duplicated(["city", "date"]).any()
    assert len(cleaned) == 2


def test_clean_records_rejects_negative_precipitation():
    payload = valid_payload()
    payload["daily"]["precipitation_sum"][0] = -1.0

    cleaned = clean_records([("Champaign", payload)])

    assert len(cleaned) == 1
    assert cleaned.iloc[0]["date"] == pd.Timestamp("2025-10-02")


def test_clean_dataframe_rejects_missing_columns():
    df = pd.DataFrame({"city": ["Champaign"], "date": ["2025-10-01"]})

    with pytest.raises(ValueError, match="Missing required columns"):
        clean_weather_dataframe(df)


def test_clean_dataframe_drops_invalid_dates_and_missing_values():
    df = pd.DataFrame(
        {
            "city": ["Champaign", "Champaign"],
            "date": ["2025-10-01", "not-a-date"],
            "temperature_max_c": [18.0, 20.0],
            "temperature_min_c": [8.0, 10.0],
            "precipitation_mm": [0.0, 1.0],
            "wind_speed_max_kmh": [12.0, 10.0],
        }
    )

    cleaned = clean_weather_dataframe(df)

    assert len(cleaned) == 1
    assert cleaned.iloc[0]["precipitation_mm"] == 0.0
