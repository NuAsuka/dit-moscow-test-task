import pandas as pd
import numpy as np
from pathlib import Path
import pandera as pa
import pandas as pd
from pandera.typing import Series
from dataclasses import dataclass
import phonenumbers
import re


class CustomerSchema(pa.DataFrameModel):
    customer_id: Series[int] = pa.Field(coerce=True, unique=True, nullable=False)
    full_name: Series[str] = pa.Field(coerce=True, nullable=False)
    email: Series[str] = pa.Field(coerce=True, nullable=True)
    phone: Series[str] = pa.Field(coerce=True, nullable=True)
    city: Series[str] = pa.Field(coerce=True, nullable=False)
    created_at: Series[pd.Timestamp] = pa.Field(coerce=True, nullable=False)

    @pa.check("full_name")
    def check_full_name_length(cls, series: Series[str]) -> Series[bool]:
        return series.str.len() >= 3

    @pa.check("email")
    def check_email_format(cls, series: Series[str]) -> Series[bool]:
        return series.str.match(r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$", na=True)

    @pa.check("phone")
    def check_phone_format(cls, series: Series[str]) -> Series[bool]:
        return series.str.match(r"^\+7\d{10}$", na=True)

    @pa.check("city")
    def check_city_length(cls, series: Series[str]) -> Series[bool]:
        return series.str.len() >= 2
    
class EventsSchema(pa.DataFrameModel):
    event_id: Series[int] = pa.Field(
        coerce=True, 
        unique=True, 
        nullable=False, 
        ge=1,
        description="Уникальный идентификатор события"
    )
    
    customer_id: Series[int] = pa.Field(
        coerce=True, 
        nullable=True, 
        ge=1,
        description="ID клиента (может быть null для анонимных пользователей)"
    )
    
    event_type: Series[str] = pa.Field(
        coerce=True, 
        nullable=False,
        isin=["view", "login", "purchase", "click", "add_to_cart", "logout", "search"],
        description="Тип события из разрешенного списка"
    )
    
    event_timestamp: Series[pd.Timestamp] = pa.Field(
        coerce=True, 
        nullable=False,
        description="Время события, приводится к формату datetime"
    )
    
    product_id: Series[int] = pa.Field(
        coerce=True, 
        nullable=True, 
        ge=1,
        description="ID продукта (может быть null, например, при событии login)"
    )

    @pa.check("event_timestamp")
    def check_timestamp_not_in_future(cls, series: Series[pd.Timestamp]) -> Series[bool]:
        return series <= pd.Timestamp.now() + pd.Timedelta(days=1)
    
class OrdersSchema(pa.DataFrameModel):
    order_id: Series[int] = pa.Field(
        coerce=True, 
        unique=True, 
        nullable=False, 
        ge=1,
        description="Уникальный идентификатор заказа"
    )
    
    customer_id: Series[int] = pa.Field(
        coerce=True, 
        nullable=True,  # Допускаем null, если возможны гостевые заказы
        ge=1,
        description="ID клиента"
    )
    
    product_id: Series[int] = pa.Field(
        coerce=True, 
        nullable=False, 
        ge=1,
        description="ID товара"
    )
    
    quantity: Series[int] = pa.Field(
        coerce=True, 
        nullable=False, 
        gt=0,  # Количество должно быть строго больше 0
        description="Количество единиц товара"
    )
    
    unit_price: Series[float] = pa.Field(
        coerce=True, 
        nullable=False, 
        ge=0.0, 
        le=1_000_000.0,  # Защита от аномальных цен (опечаток вроде 25600000.02)
        description="Цена за единицу товара"
    )
    
    currency: Series[str] = pa.Field(
        coerce=True, 
        nullable=False,
        isin=["USD", "EUR", "RUB", "GBP", "CNY"], # Белый список валют
        description="Валюта заказа"
    )
    
    order_timestamp: Series[pd.Timestamp] = pa.Field(
        coerce=True, 
        nullable=False,
        description="Время создания заказа"
    )
    
    status: Series[str] = pa.Field(
        coerce=True, 
        nullable=False,
        isin=["pending", "processing", "completed", "cancelled", "refunded", "shipped"],
        description="Статус заказа"
    )

    @pa.check("order_timestamp")
    def check_timestamp_not_in_future(cls, series: Series[pd.Timestamp]) -> Series[bool]:
        """Заказ не может быть создан в будущем (с допуском в 1 день на часовые пояса)"""
        return series <= pd.Timestamp.now() + pd.Timedelta(days=1)

    @pa.check("order_timestamp")
    def check_timestamp_not_too_old(cls, series: Series[pd.Timestamp]) -> Series[bool]:
        """Защита от аномально старых дат (например, 1970 год из-за ошибок парсинга)"""
        return series >= pd.Timestamp("2020-01-01")
    
class PaymentsSchema(pa.DataFrameModel):
    payment_id: Series[int] = pa.Field(
        coerce=True, 
        unique=True, 
        nullable=False, 
        ge=1,
        description="Уникальный идентификатор платежа"
    )
    
    order_id: Series[int] = pa.Field(
        coerce=True, 
        nullable=False, 
        ge=1,
        description="ID заказа, к которому привязан платеж"
    )
    
    payment_method: Series[str] = pa.Field(
        coerce=True, 
        nullable=False, # Платеж БЕЗ способа оплаты - это ошибка данных
        isin=["card", "paypal", "bank_transfer", "crypto", "apple_pay", "google_pay"],
        description="Способ оплаты из разрешенного списка"
    )
    
    amount: Series[float] = pa.Field(
        coerce=True, 
        nullable=False, 
        gt=0.0, # Сумма платежа должна быть строго больше нуля
        le=50_000_000.0, # Защита от аномальных выбросов (опечаток в количестве нулей)
        description="Сумма платежа"
    )
    
    currency: Series[str] = pa.Field(
        coerce=True, 
        nullable=False,
        isin=["USD", "EUR", "RUB", "GBP", "CNY", "KZT"],
        description="Валюта платежа"
    )
    
    payment_timestamp: Series[pd.Timestamp] = pa.Field(
        coerce=True, 
        nullable=False,
        description="Время совершения платежа"
    )

    # --- КАСТОМНЫЕ ПРОВЕРКИ БИЗНЕС-ЛОГИКИ ---

    @pa.check("payment_timestamp")
    def check_timestamp_not_absurd_future(cls, series: Series[pd.Timestamp]) -> Series[bool]:
        """
        Защита от некорректных дат в будущем. 
        Допускаем максимум +1 год (например, для предзаказов), 
        но это отловит ошибки вроде '2099-01-01' или сдвиги эпохи.
        """
        return series <= pd.Timestamp.now() + pd.Timedelta(days=365)

    @pa.check("payment_timestamp")
    def check_timestamp_not_too_old(cls, series: Series[pd.Timestamp]) -> Series[bool]:
        """Защита от дат до эпохи интернет-платежей (ошибки парсинга в 1970 год)"""
        return series >= pd.Timestamp("2010-01-01")

class ProductsSchema(pa.DataFrameModel):
    product_id: Series[int] = pa.Field(
        coerce=True, 
        unique=True, 
        nullable=False, 
        ge=1,
        description="Уникальный идентификатор товара"
    )
    
    product_name: Series[str] = pa.Field(
        coerce=True, 
        nullable=False,
        description="Название товара"
    )
    
    category: Series[str] = pa.Field(
        coerce=True, 
        nullable=False,
        # Строгий белый список категорий. Если придет "Электроника" вместо "Electronics", оно уйдет в карантин.
        isin=["Electronics", "Clothing", "Home", "Books", "Sports", "Toys", "Food", "Beauty", "Other"],
        description="Категория товара"
    )
    
    price: Series[float] = pa.Field(
        coerce=True, 
        nullable=False, 
        gt=0.0,          # Цена не может быть нулевой или отрицательной
        le=10_000_000.0, # Защита от опечаток (например, 5447000.00 вместо 54.47)
        description="Цена товара"
    )
    
    currency: Series[str] = pa.Field(
        coerce=True, 
        nullable=False,
        # Важно: этот список должен совпадать со списками в таблицах orders и payments для целостности данных
        isin=["USD", "EUR", "RUB", "GBP", "CNY"],
        description="Валюта цены"
    )
    
    is_active: Series[bool] = pa.Field(
        coerce=True, 
        nullable=False,
        description="Флаг активности товара (True/False)"
    )

    # --- КАСТОМНЫЕ ПРОВЕРКИ ---

    @pa.check("product_name")
    def check_name_length(cls, series: Series[str]) -> Series[bool]:
        """Название товара не может быть слишком коротким (защита от мусора вроде 'А', ' ', '-')"""
        return series.str.strip().str.len() >= 2

    @pa.check("product_name")
    def check_name_not_all_caps(cls, series: Series[str]) -> Series[bool]:
        """Опциональная проверка: название не должно быть полностью в верхнем регистре (защита от CAPS LOCK)"""
        # Разрешаем аббревиатуры до 3 символов (например, "TV", "IP"), но запрещаем длинные слова капсом
        return ~series.str.match(r'^[A-ZА-ЯЁ\s]{4,}$')