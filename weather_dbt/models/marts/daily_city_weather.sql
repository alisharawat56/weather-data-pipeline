
{{ config(materialized='table') }}

SELECT
    city_id,
    city_name,
    observation_date,
    ROUND(AVG(temperature_c), 2) AS average_temperature_c,
    ROUND(SUM(precipitation_mm), 2) AS total_precipitation_mm,
    ROUND(MAX(wind_speed_kmh), 2) AS max_wind_speed_kmh,
    COUNT(*) AS observation_count
FROM {{ ref('stg_weather_observations') }}
GROUP BY
    city_id,
    city_name,
    observation_date
