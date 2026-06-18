SELECT dc.customer_id, dc.full_name, COUNT(fo.order_key) AS total_orders, MAX(dd.full_date) AS last_order_date
FROM fact_orders fo
JOIN dim_customer dc ON fo.customer_key = dc.customer_key
JOIN dim_date dd ON fo.order_date_key = dd.date_key
GROUP BY dc.customer_key, dc.full_name
ORDER BY total_orders DESC
LIMIT 5