import pandas as pd
import numpy as np
from pathlib import Path
import pandera as pa
import pandas as pd
from pandera.typing import Series
from dataclasses import dataclass
from schemes import *
from filter import *
from tools import *
import io
import logging
import sqlite3
from dwm_create import *

conn = sqlite3.connect("data/dwh.db")

logging.basicConfig(
    filename='data/etl.log', 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s -\n%(message)s'
)

CURRENT_DIR = Path().resolve()
DATA_PATH = CURRENT_DIR / 'data'
QUARANTINE_PATH = CURRENT_DIR / 'data' / 'quarantine'
QUARANTINE_PATH.mkdir(parents=True, exist_ok=True)

CUSTOMERS_PATH = DATA_PATH / 'customers.csv'
EVENTS_PATH = DATA_PATH / 'events.xml'
ORDERS_PATH = DATA_PATH / 'orders.json'
PAYMENTS_PATH = DATA_PATH / 'payments.csv'
PRODUCTS_PATH = DATA_PATH / 'products.xlsx'


def safe_read_csv(path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(path)
        if df.empty:
            return pd.DataFrame()
        return df
    except (pd.errors.EmptyDataError, FileNotFoundError):
        return pd.DataFrame()


df = pd.read_csv(CUSTOMERS_PATH)
df.attrs["name"] = str(CUSTOMERS_PATH)
df = df.drop_duplicates()
df['phone'] = df['phone'].apply(standardize_phone_systematic)
df['city'] = standardize_city_systematic(df['city'])
df['full_name'] = df['full_name'].apply(standardize_name)
df['email'] = standardize_email_systematic(df['email'])
df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
customers_result = validate_and_quarantine(df, CustomerSchema)
customers_df = customers_result.clean_df
customers_result.quarantine_df.to_csv(QUARANTINE_PATH / 'customers_quarantine.csv', index=False)
logging.info("\n" + customers_result.summary)

df = pd.read_xml(EVENTS_PATH)
df.attrs["name"] = EVENTS_PATH
df = df.drop_duplicates()
df['event_timestamp'] = pd.to_datetime(df['event_timestamp'], errors='coerce')
events_result = validate_and_quarantine(df, EventsSchema)
events_df = events_result.clean_df
events_result.quarantine_df.to_csv(QUARANTINE_PATH / 'events_quarantine.csv', index=False)
logging.info("\n" + events_result.summary)

df = pd.read_json(ORDERS_PATH)
df.attrs["name"] = ORDERS_PATH
df = df.drop_duplicates()
df['order_timestamp'] = pd.to_datetime(df['order_timestamp'], errors='coerce')
orders_result = validate_and_quarantine(df, OrdersSchema)
orders_df = orders_result.clean_df
orders_result.quarantine_df.to_csv(QUARANTINE_PATH / 'orders_quarantine.csv', index=False)
logging.info("\n" + orders_result.summary)

df = pd.read_csv(PAYMENTS_PATH, sep='^')
df.attrs["name"] = PAYMENTS_PATH
df = df.drop_duplicates()
df['payment_timestamp'] = pd.to_datetime(df['payment_timestamp'], errors='coerce')
payments_result = validate_and_quarantine(df, PaymentsSchema)
payments_df = payments_result.clean_df
payments_result.quarantine_df.to_csv(QUARANTINE_PATH / 'payments_quarantine.csv', index=False)
logging.info("\n" + payments_result.summary)

df = pd.read_excel(PRODUCTS_PATH)
df.attrs["name"] = PRODUCTS_PATH
df = df.drop_duplicates()
products_result = validate_and_quarantine(df, ProductsSchema)
products_df = products_result.clean_df
products_result.quarantine_df.to_csv(QUARANTINE_PATH / 'products_quarantine.csv', index=False)
logging.info("\n" + products_result.summary)

customers_df.to_sql("raw_customers", conn, if_exists="replace", index=False)
events_df.to_sql("raw_events", conn, if_exists="replace", index=False)
orders_df.to_sql("raw_orders", conn, if_exists="replace", index=False)
payments_df.to_sql("raw_payments", conn, if_exists="replace", index=False)
products_df.to_sql("raw_products", conn, if_exists="replace", index=False)


def check_fk_violations(df: pd.DataFrame, fk_column: str, valid_keys: set) -> pd.DataFrame:
    if fk_column not in df.columns:
        return pd.DataFrame()
    mask = df[fk_column].notna() & ~df[fk_column].isin(valid_keys)
    return df[mask].copy()


def add_to_quarantine(quarantine_df: pd.DataFrame, new_violations: pd.DataFrame, 
                      violation_reason: str) -> pd.DataFrame:
    if new_violations.empty:
        return quarantine_df
    
    new_violations = new_violations.copy()
    new_violations['fk_violation_reason'] = violation_reason
    
    if quarantine_df.empty:
        return new_violations
    
    all_cols = list(set(quarantine_df.columns) | set(new_violations.columns))
    quarantine_df = quarantine_df.reindex(columns=all_cols)
    new_violations = new_violations.reindex(columns=all_cols, fill_value=None)
    
    return pd.concat([quarantine_df, new_violations], ignore_index=True)


customers_quarantine = safe_read_csv(QUARANTINE_PATH / 'customers_quarantine.csv')
events_quarantine = safe_read_csv(QUARANTINE_PATH / 'events_quarantine.csv')
orders_quarantine = safe_read_csv(QUARANTINE_PATH / 'orders_quarantine.csv')
payments_quarantine = safe_read_csv(QUARANTINE_PATH / 'payments_quarantine.csv')
products_quarantine = safe_read_csv(QUARANTINE_PATH / 'products_quarantine.csv')

valid_customer_ids = set(customers_df['customer_id'].dropna().unique())
valid_product_ids = set(products_df['product_id'].dropna().unique())

orders_fk_customer = check_fk_violations(orders_df, 'customer_id', valid_customer_ids)
if not orders_fk_customer.empty:
    orders_quarantine = add_to_quarantine(
        orders_quarantine, orders_fk_customer, 
        f"customer_id отсутствует в customers ({len(orders_fk_customer)} записей)"
    )
    orders_df = orders_df.drop(orders_fk_customer.index)

orders_fk_product = check_fk_violations(orders_df, 'product_id', valid_product_ids)
if not orders_fk_product.empty:
    orders_quarantine = add_to_quarantine(
        orders_quarantine, orders_fk_product, 
        f"product_id отсутствует в products ({len(orders_fk_product)} записей)"
    )
    orders_df = orders_df.drop(orders_fk_product.index)

events_fk_customer = check_fk_violations(events_df, 'customer_id', valid_customer_ids)
if not events_fk_customer.empty:
    events_quarantine = add_to_quarantine(
        events_quarantine, events_fk_customer, 
        f"customer_id отсутствует в customers ({len(events_fk_customer)} записей)"
    )
    events_df = events_df.drop(events_fk_customer.index)

events_fk_product = check_fk_violations(events_df, 'product_id', valid_product_ids)
if not events_fk_product.empty:
    events_quarantine = add_to_quarantine(
        events_quarantine, events_fk_product, 
        f"product_id отсутствует в products ({len(events_fk_product)} записей)"
    )
    events_df = events_df.drop(events_fk_product.index)

valid_order_ids = set(orders_df['order_id'].dropna().unique())

payments_fk_order = check_fk_violations(payments_df, 'order_id', valid_order_ids)
if not payments_fk_order.empty:
    payments_quarantine = add_to_quarantine(
        payments_quarantine, payments_fk_order, 
        f"order_id отсутствует в orders ({len(payments_fk_order)} записей)"
    )
    payments_df = payments_df.drop(payments_fk_order.index)

customers_quarantine.to_csv(QUARANTINE_PATH / 'customers_quarantine.csv', index=False)
events_quarantine.to_csv(QUARANTINE_PATH / 'events_quarantine.csv', index=False)
orders_quarantine.to_csv(QUARANTINE_PATH / 'orders_quarantine.csv', index=False)
payments_quarantine.to_csv(QUARANTINE_PATH / 'payments_quarantine.csv', index=False)
products_quarantine.to_csv(QUARANTINE_PATH / 'products_quarantine.csv', index=False)

orders_df.to_sql("raw_orders", conn, if_exists="replace", index=False)
events_df.to_sql("raw_events", conn, if_exists="replace", index=False)
payments_df.to_sql("raw_payments", conn, if_exists="replace", index=False)


create_star_schema(conn)
populate_star_schema(conn)
conn.close()