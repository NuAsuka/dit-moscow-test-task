import pandas as pd
import numpy as np
from pathlib import Path
import pandera as pa
import pandas as pd
from pandera.typing import Series
from dataclasses import dataclass
import phonenumbers
import re

def review_dataset(df):
    print("--- ОБЩАЯ ИНФОРМАЦИЯ ---")
    print(f"Размер датасета: {df.shape[0]} строк, {df.shape[1]} столбцов\n")

    info_df = pd.DataFrame(
        {
            "Тип данных": df.dtypes,
            "Непустые значения": df.count(),
            "Пропуски (NaN)": df.isna().sum(),
            "% Пропусков": (df.isna().sum() / len(df) * 100).round(2),
            "Уникальные": df.nunique(),
        }
    )

    print(info_df)

def base_processing(df):
    df = df.drop_duplicates()
    review_dataset(df)
    return df

def standardize_phone_systematic(phone_val):
    if pd.isna(phone_val) or str(phone_val).upper() in ['UNKNOWN', 'NaN', 'N/A', '']:
        return np.nan
    
    phone_str = str(phone_val).strip()
    
    try:
        parsed_number = phonenumbers.parse(phone_str, 'RU')
        if phonenumbers.is_valid_number(parsed_number):
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        pass
    
    return np.nan

def standardize_city_systematic(city_series):
    cleaned = (
        city_series
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r'^(п\.|ст\.|г\.|д\.|с\.|клх\.?|поселок|город|станция|деревня|село|к\.)\s*|\s*\([^)]*\)', '', regex=True)
        .str.strip()
        .str.title()
    )
    
    city_mapping = {
        'Питер': 'Санкт-Петербург',
        'Спб': 'Санкт-Петербург',
        'Мск': 'Москва',
        'Набережные Челны': 'Набережные Челны',
        'Клх Печора': 'Печора'
    }
    
    return cleaned.replace(city_mapping)

def standardize_name(name_val):
    if pd.isna(name_val) or str(name_val).upper() in ['UNKNOWN', 'NaN', 'N/A', '']:
        return np.nan
    
    name_str = str(name_val).strip()
    
    # Системное удаление распространенных обращений и мусора в начале строки
    prefixes_to_remove = r'^(г-н|Тов.)\s*'
    name_str = re.sub(prefixes_to_remove, '', name_str, flags=re.IGNORECASE)
    
    # Удаление лишних пробелов и приведение к стандартному виду (Заглавные буквы)
    return " ".join(name_str.split()).title()

def standardize_email_systematic(email_series):
    return (
        email_series
        .astype(str)
        .str.strip()
        .str.lower()
        .replace(['unknown', 'nan', 'null', ''], np.nan)
        .where(lambda x: x.str.match(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$', na=False))
    )

