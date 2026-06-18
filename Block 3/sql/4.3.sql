select dp.product_name, sum(fo.quantity) as count
from fact_orders fo
join dim_product dp on fo.product_key = dp.product_key
group by dp.product_key, dp.product_name
order by count desc
limit 15