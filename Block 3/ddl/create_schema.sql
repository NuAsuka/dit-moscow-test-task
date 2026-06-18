DROP TABLE IF EXISTS fact_events;
DROP TABLE IF EXISTS fact_orders;
DROP TABLE IF EXISTS fact_payments;
DROP TABLE IF EXISTS dim_customer;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_time;
DROP TABLE IF EXISTS dim_order_status;

CREATE TABLE dim_customer (
    customer_key INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER UNIQUE,
    full_name TEXT,
    email TEXT,
    phone TEXT,
    city TEXT,
    created_at TEXT,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_product (
    product_key INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER UNIQUE,
    product_name TEXT,
    category TEXT,
    price REAL,
    currency TEXT,
    is_active INTEGER,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date TEXT,
    year INTEGER,
    month INTEGER,
    day INTEGER,
    day_of_week TEXT,
    is_weekend INTEGER
);

CREATE TABLE dim_time (
    time_key INTEGER PRIMARY KEY,
    hour INTEGER,
    minute INTEGER,
    second INTEGER
);

CREATE TABLE dim_order_status (
    status_key INTEGER PRIMARY KEY AUTOINCREMENT,
    status_name TEXT UNIQUE
);

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
);

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
);

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
);

CREATE INDEX idx_fact_orders_customer ON fact_orders(customer_key);
CREATE INDEX idx_fact_orders_product ON fact_orders(product_key);
CREATE INDEX idx_fact_orders_date ON fact_orders(order_date_key);
CREATE INDEX idx_fact_events_customer ON fact_events(customer_key);
CREATE INDEX idx_fact_events_product ON fact_events(product_key);
CREATE INDEX idx_fact_events_date ON fact_events(event_date_key);
CREATE INDEX idx_fact_payments_date ON fact_payments(payment_date_key);