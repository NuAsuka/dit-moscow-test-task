select full_name, sum(total_amount) as buy_sum
from fact_orders
join dim_customer using(customer_key)
group by customer_key, full_name
order by buy_sum desc
limit 10