
-- Query 1: Average weather measurements by city

SELECT
    c.name AS city,
    ROUND(AVG(w.temperature_c)::numeric, 2) AS avg_temperature_c,
    ROUND(AVG(w.precipitation_mm)::numeric, 2) AS avg_precipitation_mm,
    ROUND(AVG(w.wind_speed_kmh)::numeric, 2) AS avg_wind_speed_kmh
FROM public.weather_observations w
JOIN public.cities c
    ON w.city_id = c.city_id
GROUP BY c.name
ORDER BY c.name;


-- Query 2: Top 10 days with highest precipitation

SELECT
    c.name AS city,
    w.observation_timestamp,
    w.precipitation_mm
FROM public.weather_observations w
JOIN public.cities c
    ON w.city_id = c.city_id
ORDER BY w.precipitation_mm DESC
LIMIT 10;


-- Query 3: Observation count by city

SELECT
    c.name AS city,
    COUNT(w.observation_id) AS observation_count
FROM public.cities c
LEFT JOIN public.weather_observations w
    ON c.city_id = w.city_id
GROUP BY c.name
ORDER BY c.name;


-- Query 4: Highest recorded temperature by city

SELECT
    c.name AS city,
    MAX(w.temperature_c) AS highest_temperature_c
FROM public.weather_observations w
JOIN public.cities c
    ON w.city_id = c.city_id
GROUP BY c.name
ORDER BY highest_temperature_c DESC;

