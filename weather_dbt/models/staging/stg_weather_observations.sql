
{{ config(materialized='view') }}

SELECT
    w.observation_id,
    w.city_id,
    c.name AS city_name,
    w.observation_timestamp::date AS observation_date,
    w.temperature_c,
    w.precipitation_mm,
    w.wind_speed_kmh
FROM {{ source('weather', 'weather_observations') }} AS w
JOIN {{ source('weather', 'cities') }} AS c
    ON w.city_id = c.city_id
