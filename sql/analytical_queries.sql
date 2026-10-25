
-- 1. Average temperature by city
SELECT
    c.name AS city,
    ROUND(AVG(w.temperature_c), 2) AS avg_temperature_c
FROM weather_observations AS w
JOIN cities AS c ON c.city_id = w.city_id
GROUP BY c.name
ORDER BY avg_temperature_c DESC;


-- 2. Total precipitation by city
SELECT
    c.name AS city,
    ROUND(SUM(w.precipitation_mm), 2) AS total_precipitation_mm
FROM weather_observations AS w
JOIN cities AS c ON c.city_id = w.city_id
GROUP BY c.name
ORDER BY total_precipitation_mm DESC;


-- 3. Daily temperature trends by city
SELECT
    c.name AS city,
    w.observation_timestamp::date AS observation_date,
    ROUND(AVG(w.temperature_c), 2) AS avg_temperature_c
FROM weather_observations AS w
JOIN cities AS c ON c.city_id = w.city_id
GROUP BY c.name, w.observation_timestamp::date
ORDER BY city, observation_date;


-- 4. Cities ranked by average wind speed
SELECT
    c.name AS city,
    ROUND(AVG(w.wind_speed_kmh), 2) AS avg_wind_speed_kmh
FROM weather_observations AS w
JOIN cities AS c ON c.city_id = w.city_id
GROUP BY c.name
ORDER BY avg_wind_speed_kmh DESC;


-- 5. Temperature changes between consecutive observations
SELECT
    c.name AS city,
    w.observation_timestamp,
    w.temperature_c,
    LAG(w.temperature_c) OVER (
        PARTITION BY w.city_id
        ORDER BY w.observation_timestamp
    ) AS previous_temperature_c,
    ROUND(
        w.temperature_c - LAG(w.temperature_c) OVER (
            PARTITION BY w.city_id
            ORDER BY w.observation_timestamp
        ),
        2
    ) AS temperature_change_c
FROM weather_observations AS w
JOIN cities AS c ON c.city_id = w.city_id
ORDER BY city, w.observation_timestamp;
