
SELECT
    city_id,
    observation_date,
    COUNT(*) AS row_count
FROM {{ ref('daily_city_weather') }}
GROUP BY
    city_id,
    observation_date
HAVING COUNT(*) > 1
