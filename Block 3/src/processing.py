import pandas as pd
import numpy as np
from pathlib import Path
import pandera as pa
import pandas as pd
from pandera.typing import Series
from dataclasses import dataclass
import phonenumbers
import re
from schemes import *
from filter import *
from tools import *

current_dir = Path().resolve().parent
DATA_PATH = current_dir / 'data'

CUSTOMERS_PATH = DATA_PATH / 'customers.csv'
EVENTS_PATH = DATA_PATH / 'events.xml'
ORDERS_PATH = DATA_PATH / 'orders.json'
PAYMENTS_PATH = DATA_PATH / 'payments.csv'
PRODUCTS_PATH = DATA_PATH / 'products.xlsx'


df = pd.read_csv(CUSTOMERS_PATH)
df = df.drop_duplicates()
df['phone'] = df['phone'].apply(standardize_phone_systematic)
df['city'] = standardize_city_systematic(df['city'])
df['full_name'] = df['full_name'].apply(standardize_name)
df['email'] = standardize_email_systematic(df['email'])
df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
customers_result = validate_and_quarantine(df, CustomerSchema)
customers_df = customers_result.clean_df

df = pd.read_xml(EVENTS_PATH)
df = df.drop_duplicates()
events_result = validate_and_quarantine(df, EventsSchema)
events_df = events_result.clean_df

df = pd.read_json(ORDERS_PATH)
df = df.drop_duplicates()
orders_result = validate_and_quarantine(df, OrdersSchema)
orders_df = orders_result.clean_df

df = pd.read_csv(PAYMENTS_PATH,sep='^')
df = df.drop_duplicates()
payments_result = validate_and_quarantine(df, PaymentsSchema)
payments_df = payments_result.clean_df

df = pd.read_excel(PRODUCTS_PATH)
df = df.drop_duplicates()
products_result = validate_and_quarantine(df, ProductsSchema)
products_df = products_result.clean_df
