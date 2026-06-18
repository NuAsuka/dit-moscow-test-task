select dc.customer_key, dc.full_name
from dim_customer dc
where (dc.customer_key not in (select distinct customer_key from fact_orders))