# ETL Pipeline with Data Quality & Star Schema DWH

MVP проект по очистки данных и загрузки в спроектированную DWH-модель за 5 часов. Проект реализует ETL-процесс (Extract, Transform, Load) с механизмом контроля качества данных (Data Quality) и загрузкой в хранилище данных на основе **Star Schema**. Применяется стек Python + SQLite


## Структура проекта

```
.
├── data/
│   ├── customers.csv          # Исходные данные: клиенты
│   ├── events.xml             # Исходные данные: события
│   ├── orders.json            # Исходные данные: заказы
│   ├── payments.csv           # Исходные данные: платежи
│   ├── products.xlsx          # Исходные данные: товары
│   ├── dwh.db                 # SQLite база данных (результат)
│   ├── etl.log                # Лог процесса ETL
│   └── quarantine/            # "Грязные" данные, не прошедшие валидацию
│       ├── customers_quarantine.csv
│       ├── events_quarantine.csv
│       ├── orders_quarantine.csv
│       ├── payments_quarantine.csv
│       └── products_quarantine.csv
├── ddl/
│   ├── create_schema.sql      # DDL: создание таблиц Star Schema
│   └── populate_schema.sql    # DML: заполнение таблиц данными
├── sql/
│   ├── 4.1.sql                # Топ-10 клиентов по сумме покупок
│   ├── 4.2.sql                # Выручка по месяцам
│   ├── 4.3.sql                # Самые популярные товары
│   ├── 4.4.sql                # Последняя активность топ-5 покупателей
│   └── 4.5.sql                # Пользователи без заказов
├── src/
│   ├── main.py                # Основной ETL-пайплайн
│   ├── schemes.py             # Схемы валидации Pandera
│   ├── filter.py              # Функции валидации и карантина
│   ├── tools.py               # Утилиты очистки данных
│   ├── dwm_create.py          # Создание и заполнение Star Schema
│   └── mvp.ipynb              # Jupyter Notebook для исследований
├── requirements.txt           # Зависимости Python
└── README.md                  # Документация
```

## Установка и запуск

### Требования

- Python 3.10+

### Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/NuAsuka/dit-moscow-test-task/tree/main/Block%203
cd Block-3
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Запуск

```bash
python src/main.py
```

После выполнения:
- База данных создастся в `data/dwh.db`
- Лог процесса сохранится в `data/etl.log`
- Проблемные записи попадут в `data/quarantine/`

## Архитектурные решения

### Слои данных

1. **Raw Layer** (`raw_*` таблицы) — исходные данные после первичной очистки
2. **DWH Layer** (Star Schema) — аналитическая модель данных

### Ключевые решения

- **Pandera** для декларативной валидации схем данных
- **Quarantine Pattern** — автоматическое разделение данных на "чистые" и "грязные"
- **Star Schema** — оптимизированная модель для аналитических запросов
- **SQL DDL/DML** вынесены в отдельные файлы для удобства поддержки
- **Каскадная проверка FK** — заказы удаляются, если нет клиента/товара; платежи удаляются, если нет заказа

## Data Quality и валидация

### Реализованные проверки

- **Удаление дубликатов** — `.drop_duplicates()` для всех источников
- **Not Null проверки** — обязательные поля (ID, даты, суммы)
- **Валидация типов** — приведение дат к TIMESTAMP, чисел к INT/FLOAT
- **Бизнес-логика** — цены >= 0, количества > 0, валидные email/телефоны
- **Внешние ключи** — проверка ссылочной целостности между таблицами

### Механизм Quarantine

Все записи, не прошедшие валидацию:
1. Автоматически исключаются из основного потока
2. Сохраняются в `data/quarantine/*.csv`
3. Логируются в `data/etl.log` с подробным описанием причины.

### Принятые решения по источникам

#### 1. customers.csv
- **Очистка ФИО** — удаление обращений ("г-н", "товарищ"). Имеются записи Ivan Ivanov, было решение их оставить, поскольку фио формально есть.
- **Телефоны** — 281 запись с пустыми phone сохранена (40% данных)
- **Необязательные поля** — email, city, created_at могут быть NULL

#### 2. events.xml
- **BAD_ID** — записи с некорректным event_id отправлены в карантин
- **Даты** — 51 запись с "broken-date" или NaT отправлена в карантин
- **Customer ID** — пропуски недопустимы (карантин)

#### 3. orders.json
- **Некорректные даты** — "2025-99-99" отправлено в карантин
- **Customer ID** — 54 записи с NULL отправлены в карантин

#### 4. payments.csv
- **Суммы** — "error_amount" отправлено в карантин
- **Способ оплаты** — 268 записей без payment_method (критично для финансов)
- **Даты** — "13/45/2025" отправлено в карантин

#### 5. products.xlsx
- **Названия** — product_name < 2 символов ("О") отправлено в карантин
- **Цены** — 19 записей с NULL price отправлено в карантин

### Логирование

Подробный лог доступен в `data/etl.log`:
- Статистика по каждому источнику (всего/очищено/карантин)
- Детали ошибок валидации
- Результаты проверки внешних ключей

##  Модель данных (Star Schema)

### Таблицы измерений (Dimensions)

- **dim_customer** — клиенты (customer_key, customer_id, full_name, email, phone, city)
- **dim_product** — товары (product_key, product_id, product_name, category, price)
- **dim_date** — даты (date_key, full_date, year, month, day, day_of_week, is_weekend)
- **dim_time** — время (time_key, hour, minute, second)
- **dim_order_status** — статусы заказов (status_key, status_name)

### Таблицы фактов (Facts)

- **fact_orders** — заказы (order_key, order_id, customer_key, product_key, status_key, quantity, unit_price, total_amount, currency, order_date_key, order_time_key)
- **fact_events** — события (event_key, event_id, customer_key, product_key, event_type, event_date_key, event_time_key)
- **fact_payments** — платежи (payment_key, payment_id, order_id, payment_method, amount, currency, payment_date_key, payment_time_key)



## SQL-запросы

Запросы из задания доступны в папке `sql/`:

### 1. Топ-10 клиентов по сумме покупок

```sql
SELECT 
    dc.customer_id,
    dc.full_name, 
    SUM(fo.total_amount) AS buy_sum
FROM fact_orders fo
JOIN dim_customer dc ON fo.customer_key = dc.customer_key
GROUP BY dc.customer_key, dc.full_name
ORDER BY buy_sum DESC
LIMIT 10
```

### 2. Выручка по месяцам

```sql
SELECT 
    dd.year,
    dd.month,
    SUM(fo.total_amount) AS revenue
FROM fact_orders fo
JOIN dim_date dd ON fo.order_date_key = dd.date_key
GROUP BY dd.year, dd.month
ORDER BY dd.year, dd.month
```

### 3. Самые популярные товары

```sql
SELECT 
    dp.product_name,
    SUM(fo.quantity) AS units_sold
FROM fact_orders fo
JOIN dim_product dp ON fo.product_key = dp.product_key
GROUP BY dp.product_key, dp.product_name
ORDER BY units_sold DESC
LIMIT 10
```

### 4. Последняя активность топ-5 покупателей

```sql
SELECT 
    dc.customer_id,
    dc.full_name,
    COUNT(fo.order_key) AS total_orders,
    MAX(dd.full_date) AS last_order_date
FROM fact_orders fo
JOIN dim_customer dc ON fo.customer_key = dc.customer_key
JOIN dim_date dd ON fo.order_date_key = dd.date_key
GROUP BY dc.customer_key, dc.full_name
ORDER BY total_orders DESC
LIMIT 5
```

### 5. Пользователи без заказов

```sql
SELECT 
    dc.customer_key, 
    dc.full_name
FROM dim_customer dc
WHERE NOT EXISTS (
    SELECT 1 
    FROM fact_orders fo 
    WHERE fo.customer_key = dc.customer_key
)
```

---

## Воспроизведение результата

```bash
# 1. Удалить старую базу данных
rm data/dwh.db
rm data/etl.log
rm data/quarantine/*.csv

# 2. Запустить ETL заново
python src/main.py
```


## Зависимости

Основные библиотеки:

- **pandas==3.0.3** — обработка данных
- **pandera==0.31.1** — валидация схем данных
- **numpy==2.4.6** — числовые операции
- **phonenumbers==9.0.32** — валидация телефонов
- **openpyxl==3.1.5** — работа с Excel
- **lxml==6.1.1** — парсинг XML

# Общение с ИИ

https://chat.qwen.ai/s/052b95e8-e4ae-4f5a-9504-0fe4d5034c50?fev=0.2.65