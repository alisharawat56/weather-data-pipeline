
-- Weather pipeline: three-layer architecture
-- raw -> staging -> marts

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;

-- ==========================================
-- RAW LAYER
-- One row = one API response captured during an ingestion.
-- Primary key = ingestion_id.
-- ==========================================

CREATE TABLE IF NOT EXISTS raw.weather_api_responses (
    ingestion_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    city_name TEXT NOT NULL,
    requested_start_date DATE NOT NULL,
    requested_end_date DATE NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL,
    CHECK (requested_end_date >= requested_start_date)
);

-- ==========================================
-- STAGING LAYER
-- One row = one cleaned daily observation for one city.
-- Primary key = (city_name, observation_date).
-- ==========================================

CREATE TABLE IF NOT EXISTS staging.daily_weather (
    city_name TEXT NOT NULL,
    observation_date DATE NOT NULL,
    temperature_max_c NUMERIC(5, 2),
    temperature_min_c NUMERIC(5, 2),
    precipitation_mm NUMERIC(8, 2),
    wind_speed_max_kmh NUMERIC(7, 2),

    PRIMARY KEY (city_name, observation_date),

    CHECK (
        temperature_max_c IS NULL
        OR temperature_min_c IS NULL
        OR temperature_max_c >= temperature_min_c
    ),
    CHECK (precipitation_mm IS NULL OR precipitation_mm >= 0),
    CHECK (wind_speed_max_kmh IS NULL OR wind_speed_max_kmh >= 0)
);

-- ==========================================
-- MARTS LAYER
-- Dimension: one row = one distinct city.
-- Primary key = city_id.
-- ==========================================

CREATE TABLE IF NOT EXISTS marts.dim_city (
    city_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    city_name TEXT NOT NULL UNIQUE
);

-- One row = one city on one observation date.
-- Primary key = (city_id, observation_date).
-- Designed for reporting and analytical SQL.

CREATE TABLE IF NOT EXISTS marts.fact_daily_weather (
    city_id BIGINT NOT NULL REFERENCES marts.dim_city(city_id),
    observation_date DATE NOT NULL,
    average_temperature_c NUMERIC(5, 2),
    precipitation_mm NUMERIC(8, 2),
    max_wind_speed_kmh NUMERIC(7, 2),

    PRIMARY KEY (city_id, observation_date)
);
