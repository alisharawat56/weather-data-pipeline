
CREATE TABLE IF NOT EXISTS cities (
    city_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    latitude NUMERIC(8, 5) NOT NULL,
    longitude NUMERIC(8, 5) NOT NULL,

    CONSTRAINT unique_city_location
        UNIQUE (name, country),

    CONSTRAINT valid_latitude
        CHECK (latitude BETWEEN -90 AND 90),

    CONSTRAINT valid_longitude
        CHECK (longitude BETWEEN -180 AND 180)
);

CREATE TABLE IF NOT EXISTS weather_observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    city_id INTEGER NOT NULL
        REFERENCES cities(city_id) ON DELETE CASCADE,
    observation_timestamp TIMESTAMP NOT NULL,
    temperature_c NUMERIC(5, 2),
    precipitation_mm NUMERIC(8, 2),
    wind_speed_kmh NUMERIC(7, 2),

    CONSTRAINT unique_city_observation
        UNIQUE (city_id, observation_timestamp),

    CONSTRAINT nonnegative_precipitation
        CHECK (precipitation_mm IS NULL OR precipitation_mm >= 0),

    CONSTRAINT nonnegative_wind_speed
        CHECK (wind_speed_kmh IS NULL OR wind_speed_kmh >= 0)
);
