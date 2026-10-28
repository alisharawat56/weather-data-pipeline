
-- Measurement constraints use the source units:
-- temperature: degrees Celsius
-- precipitation: millimeters
-- wind speed: kilometers per hour
--
-- The temperature envelope is intentionally broad (-50 to 50 C)
-- for the project's three US cities. Zero precipitation and zero wind
-- speed are valid values.

SELECT
    observation_id,
    city_id,
    observation_timestamp,
    temperature_c,
    precipitation_mm,
    wind_speed_kmh
FROM {{ source('weather', 'weather_observations') }}
WHERE
       temperature_c < -50
    OR temperature_c > 50
    OR precipitation_mm < 0
    OR wind_speed_kmh < 0
