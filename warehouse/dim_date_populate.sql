-- Populate dim_date calendar table for 2024 to 2027
INSERT INTO dim_date (
    date_key,
    year,
    quarter,
    month,
    month_name,
    week,
    day,
    day_name,
    is_weekend
)
SELECT 
    d::DATE AS date_key,
    EXTRACT(YEAR FROM d)::INT AS year,
    EXTRACT(QUARTER FROM d)::INT AS quarter,
    EXTRACT(MONTH FROM d)::INT AS month,
    TO_CHAR(d, 'Month') AS month_name,
    EXTRACT(WEEK FROM d)::INT AS week,
    EXTRACT(DAY FROM d)::INT AS day,
    TO_CHAR(d, 'Day') AS day_name,
    CASE WHEN EXTRACT(ISODOW FROM d) IN (6, 7) THEN TRUE ELSE FALSE END AS is_weekend
FROM generate_series('2024-01-01'::DATE, '2027-12-31'::DATE, '1 day'::INTERVAL) d
ON CONFLICT (date_key) DO NOTHING;
