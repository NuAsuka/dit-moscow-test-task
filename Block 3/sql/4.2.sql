select dd.year, dd.month, sum(fo.total_amount) as revenue
from fact_orders fo
join dim_date dd on fo.order_date_key = dd.date_key
group by dd.year, dd.month