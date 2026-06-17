import sqlite3
import pandas as pd


def create_star_schema(conn):
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS fact_events")
    cursor.execute("DROP TABLE IF EXISTS fact_orders")
    cursor.execute("DROP TABLE IF EXISTS fact_payments")
    cursor.execute("DROP TABLE IF EXISTS dim_customer")
    cursor.execute("DROP TABLE IF EXISTS dim_product")
    cursor.execute("DROP TABLE IF EXISTS dim_date")
    cursor.execute("DROP TABLE IF EXISTS dim_time")
    cursor.execute("DROP TABLE IF EXISTS dim_order_status")
    
    cursor.execute("""
        CREATE TABLE dim_customer (
            customer_key INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER UNIQUE,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            city TEXT,
            created_at TEXT,
            loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE dim_product (
            product_key INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER UNIQUE,
            product_name TEXT,
            category TEXT,
            price REAL,
            currency TEXT,
            is_active INTEGER,
            loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE dim_date (
            date_key INTEGER PRIMARY KEY,
            full_date TEXT,
            year INTEGER,
            month INTEGER,
            day INTEGER,
            day_of_week TEXT,
            is_weekend INTEGER
        )
    """)
    
    cursor.execute("""
        CREATE TABLE dim_time (
            time_key INTEGER PRIMARY KEY,
            hour INTEGER,
            minute INTEGER,
            second INTEGER
        )
    """)
    
    cursor.execute("""
        CREATE TABLE dim_order_status (
            status_key INTEGER PRIMARY KEY AUTOINCREMENT,
            status_name TEXT UNIQUE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE fact_orders (
            order_key INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            customer_key INTEGER,
            product_key INTEGER,
            status_key INTEGER,
            quantity INTEGER,
            unit_price REAL,
            total_amount REAL,
            currency TEXT,
            order_date_key INTEGER,
            order_time_key INTEGER,
            FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
            FOREIGN KEY (product_key) REFERENCES dim_product(product_key),
            FOREIGN KEY (status_key) REFERENCES dim_order_status(status_key),
            FOREIGN KEY (order_date_key) REFERENCES dim_date(date_key),
            FOREIGN KEY (order_time_key) REFERENCES dim_time(time_key)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE fact_events (
            event_key INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            customer_key INTEGER,
            product_key INTEGER,
            event_type TEXT,
            event_date_key INTEGER,
            event_time_key INTEGER,
            FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
            FOREIGN KEY (product_key) REFERENCES dim_product(product_key),
            FOREIGN KEY (event_date_key) REFERENCES dim_date(date_key),
            FOREIGN KEY (event_time_key) REFERENCES dim_time(time_key)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE fact_payments (
            payment_key INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_id INTEGER,
            order_id INTEGER,
            payment_method TEXT,
            amount REAL,
            currency TEXT,
            payment_date_key INTEGER,
            payment_time_key INTEGER,
            FOREIGN KEY (payment_date_key) REFERENCES dim_date(date_key),
            FOREIGN KEY (payment_time_key) REFERENCES dim_time(time_key)
        )
    """)
    
    cursor.execute("CREATE INDEX idx_fact_orders_customer ON fact_orders(customer_key)")
    cursor.execute("CREATE INDEX idx_fact_orders_product ON fact_orders(product_key)")
    cursor.execute("CREATE INDEX idx_fact_orders_date ON fact_orders(order_date_key)")
    cursor.execute("CREATE INDEX idx_fact_events_customer ON fact_events(customer_key)")
    cursor.execute("CREATE INDEX idx_fact_events_product ON fact_events(product_key)")
    cursor.execute("CREATE INDEX idx_fact_events_date ON fact_events(event_date_key)")
    cursor.execute("CREATE INDEX idx_fact_payments_date ON fact_payments(payment_date_key)")
    
    conn.commit()


def populate_star_schema(conn):
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR IGNORE INTO dim_customer (customer_id, full_name, email, phone, city, created_at)
        SELECT customer_id, full_name, email, phone, city, created_at
        FROM raw_customers
    """)
    
    cursor.execute("""
        INSERT OR IGNORE INTO dim_product (product_id, product_name, category, price, currency, is_active)
        SELECT product_id, product_name, category, price, currency, is_active
        FROM raw_products
    """)
    
    cursor.execute("""
        INSERT OR IGNORE INTO dim_order_status (status_name)
        SELECT DISTINCT status FROM raw_orders
    """)
    
    cursor.execute("""
        INSERT OR IGNORE INTO dim_date (date_key, full_date, year, month, day, day_of_week, is_weekend)
        SELECT 
            CAST(strftime('%Y%m%d', event_timestamp) AS INTEGER) as date_key,
            date(event_timestamp) as full_date,
            CAST(strftime('%Y', event_timestamp) AS INTEGER) as year,
            CAST(strftime('%m', event_timestamp) AS INTEGER) as month,
            CAST(strftime('%d', event_timestamp) AS INTEGER) as day,
            CASE CAST(strftime('%w', event_timestamp) AS INTEGER)
                WHEN 0 THEN 'Sunday'
                WHEN 1 THEN 'Monday'
                WHEN 2 THEN 'Tuesday'
                WHEN 3 THEN 'Wednesday'
                WHEN 4 THEN 'Thursday'
                WHEN 5 THEN 'Friday'
                WHEN 6 THEN 'Saturday'
            END as day_of_week,
            CASE WHEN CAST(strftime('%w', event_timestamp) AS INTEGER) IN (0, 6) THEN 1 ELSE 0 END as is_weekend
        FROM raw_events
        WHERE event_timestamp IS NOT NULL
        
        UNION
        
        SELECT 
            CAST(strftime('%Y%m%d', order_timestamp) AS INTEGER) as date_key,
            date(order_timestamp) as full_date,
            CAST(strftime('%Y', order_timestamp) AS INTEGER) as year,
            CAST(strftime('%m', order_timestamp) AS INTEGER) as month,
            CAST(strftime('%d', order_timestamp) AS INTEGER) as day,
            CASE CAST(strftime('%w', order_timestamp) AS INTEGER)
                WHEN 0 THEN 'Sunday'
                WHEN 1 THEN 'Monday'
                WHEN 2 THEN 'Tuesday'
                WHEN 3 THEN 'Wednesday'
                WHEN 4 THEN 'Thursday'
                WHEN 5 THEN 'Friday'
                WHEN 6 THEN 'Saturday'
            END as day_of_week,
            CASE WHEN CAST(strftime('%w', order_timestamp) AS INTEGER) IN (0, 6) THEN 1 ELSE 0 END as is_weekend
        FROM raw_orders
        WHERE order_timestamp IS NOT NULL
        
        UNION
        
        SELECT 
            CAST(strftime('%Y%m%d', payment_timestamp) AS INTEGER) as date_key,
            date(payment_timestamp) as full_date,
            CAST(strftime('%Y', payment_timestamp) AS INTEGER) as year,
            CAST(strftime('%m', payment_timestamp) AS INTEGER) as month,
            CAST(strftime('%d', payment_timestamp) AS INTEGER) as day,
            CASE CAST(strftime('%w', payment_timestamp) AS INTEGER)
                WHEN 0 THEN 'Sunday'
                WHEN 1 THEN 'Monday'
                WHEN 2 THEN 'Tuesday'
                WHEN 3 THEN 'Wednesday'
                WHEN 4 THEN 'Thursday'
                WHEN 5 THEN 'Friday'
                WHEN 6 THEN 'Saturday'
            END as day_of_week,
            CASE WHEN CAST(strftime('%w', payment_timestamp) AS INTEGER) IN (0, 6) THEN 1 ELSE 0 END as is_weekend
        FROM raw_payments
        WHERE payment_timestamp IS NOT NULL
    """)
    
    cursor.execute("""
        INSERT OR IGNORE INTO dim_time (time_key, hour, minute, second)
        SELECT 
            CAST(strftime('%H%M%S', event_timestamp) AS INTEGER) as time_key,
            CAST(strftime('%H', event_timestamp) AS INTEGER) as hour,
            CAST(strftime('%M', event_timestamp) AS INTEGER) as minute,
            CAST(strftime('%S', event_timestamp) AS INTEGER) as second
        FROM raw_events
        WHERE event_timestamp IS NOT NULL
        
        UNION
        
        SELECT 
            CAST(strftime('%H%M%S', order_timestamp) AS INTEGER) as time_key,
            CAST(strftime('%H', order_timestamp) AS INTEGER) as hour,
            CAST(strftime('%M', order_timestamp) AS INTEGER) as minute,
            CAST(strftime('%S', order_timestamp) AS INTEGER) as second
        FROM raw_orders
        WHERE order_timestamp IS NOT NULL
        
        UNION
        
        SELECT 
            CAST(strftime('%H%M%S', payment_timestamp) AS INTEGER) as time_key,
            CAST(strftime('%H', payment_timestamp) AS INTEGER) as hour,
            CAST(strftime('%M', payment_timestamp) AS INTEGER) as minute,
            CAST(strftime('%S', payment_timestamp) AS INTEGER) as second
        FROM raw_payments
        WHERE payment_timestamp IS NOT NULL
    """)
    
    cursor.execute("""
        INSERT INTO fact_orders (order_id, customer_key, product_key, status_key, quantity, unit_price, total_amount, currency, order_date_key, order_time_key)
        SELECT 
            ro.order_id,
            dc.customer_key,
            dp.product_key,
            dos.status_key,
            ro.quantity,
            ro.unit_price,
            ro.quantity * ro.unit_price as total_amount,
            ro.currency,
            CAST(strftime('%Y%m%d', ro.order_timestamp) AS INTEGER) as order_date_key,
            CAST(strftime('%H%M%S', ro.order_timestamp) AS INTEGER) as order_time_key
        FROM raw_orders ro
        LEFT JOIN dim_customer dc ON ro.customer_id = dc.customer_id
        LEFT JOIN dim_product dp ON ro.product_id = dp.product_id
        LEFT JOIN dim_order_status dos ON ro.status = dos.status_name
        WHERE ro.order_timestamp IS NOT NULL
    """)
    
    cursor.execute("""
        INSERT INTO fact_events (event_id, customer_key, product_key, event_type, event_date_key, event_time_key)
        SELECT 
            re.event_id,
            dc.customer_key,
            dp.product_key,
            re.event_type,
            CAST(strftime('%Y%m%d', re.event_timestamp) AS INTEGER) as event_date_key,
            CAST(strftime('%H%M%S', re.event_timestamp) AS INTEGER) as event_time_key
        FROM raw_events re
        LEFT JOIN dim_customer dc ON re.customer_id = dc.customer_id
        LEFT JOIN dim_product dp ON re.product_id = dp.product_id
        WHERE re.event_timestamp IS NOT NULL
    """)
    
    cursor.execute("""
        INSERT INTO fact_payments (payment_id, order_id, payment_method, amount, currency, payment_date_key, payment_time_key)
        SELECT 
            rp.payment_id,
            rp.order_id,
            rp.payment_method,
            rp.amount,
            rp.currency,
            CAST(strftime('%Y%m%d', rp.payment_timestamp) AS INTEGER) as payment_date_key,
            CAST(strftime('%H%M%S', rp.payment_timestamp) AS INTEGER) as payment_time_key
        FROM raw_payments rp
        WHERE rp.payment_timestamp IS NOT NULL
    """)
    
    conn.commit()