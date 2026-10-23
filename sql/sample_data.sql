
INSERT INTO cities (name, country, latitude, longitude)
VALUES
    ('Champaign', 'USA', 40.11640, -88.24340),
    ('Chicago', 'USA', 41.87810, -87.62980),
    ('New York', 'USA', 40.71280, -74.00600)
ON CONFLICT (name, country) DO NOTHING;


INSERT INTO weather_observations (
    city_id,
    observation_timestamp,
    temperature_c,
    precipitation_mm,
    wind_speed_kmh
)
SELECT
    c.city_id,
    sample.observation_timestamp,
    sample.temperature_c,
    sample.precipitation_mm,
    sample.wind_speed_kmh
FROM (
    VALUES
        ('Champaign', '2025-10-01 12:00:00'::timestamp,
         18.50::numeric, 0.00::numeric, 12.40::numeric),
        ('Chicago', '2025-10-01 12:00:00'::timestamp,
         16.30::numeric, 2.40::numeric, 18.20::numeric),
        ('New York', '2025-10-01 12:00:00'::timestamp,
         19.70::numeric, 1.20::numeric, 14.60::numeric)
) AS sample(
    city_name,
    observation_timestamp,
    temperature_c,
    precipitation_mm,
    wind_speed_kmh
)
JOIN cities c ON c.name = sample.city_name
    AND c.country = 'USA'
ON CONFLICT (city_id, observation_timestamp) DO NOTHING;
