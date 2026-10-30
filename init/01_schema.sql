CREATE TABLE IF NOT EXISTS cities (
    city_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    CONSTRAINT unique_city_country UNIQUE (name, country)
);

CREATE TABLE IF NOT EXISTS weather_observations (
    observation_id SERIAL PRIMARY KEY,
    city_id INTEGER NOT NULL REFERENCES cities(city_id),
    observation_timestamp DATE NOT NULL,
    temperature_c DOUBLE PRECISION,
    precipitation_mm DOUBLE PRECISION,
    wind_speed_kmh DOUBLE PRECISION,
    CONSTRAINT unique_city_observation
        UNIQUE (city_id, observation_timestamp)
);