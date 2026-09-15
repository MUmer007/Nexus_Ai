{{ config(materialized='table') }}

WITH daily_orders AS (
    SELECT 
        CAST(order_timestamp AS DATE) AS order_date,
        status_category,
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(total_amount) AS total_revenue,
        SUM(CASE WHEN status = 'COMPLETED' THEN total_amount ELSE 0 END) AS fulfilled_revenue
    FROM read_parquet('D:\nexus-ai\data\lakehouse\silver\orders\*.parquet')
    GROUP BY 1, 2
),
daily_summary AS (
    SELECT 
        order_date,
        SUM(total_orders) AS total_orders,
        SUM(total_revenue) AS total_revenue,
        SUM(fulfilled_revenue) AS fulfilled_revenue,
        -- Safe division for DuckDB (prevents division by zero)
        SUM(fulfilled_revenue) * 1.0 / NULLIF(SUM(total_revenue), 0) AS revenue_fill_rate
    FROM daily_orders
    GROUP BY 1
)
SELECT * FROM daily_summary
