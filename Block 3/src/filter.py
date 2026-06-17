import pandas as pd
import numpy as np
from pathlib import Path
import pandera.pandas as pa
from pandera.typing import Series
from dataclasses import dataclass
import phonenumbers
import re
from schemes import *
from tools import *
import io

@dataclass
class ValidationResult:
    is_valid: bool
    clean_df: pd.DataFrame
    quarantine_df: pd.DataFrame
    error_report: pd.DataFrame
    summary: str

def _build_comparison_report(original_df: pd.DataFrame, clean_df: pd.DataFrame) -> str:
    """Создает текстовый отчет сравнения метрик исходного и очищенного датафрейма"""
    lines = [
        "Столбец               | Тип данных (Исх -> Чист) | Пропуски (Исх -> Чист)",
        "-" * 78
    ]
    
    for col in original_df.columns:
        orig_dtype = str(original_df[col].dtype)
        clean_dtype = str(clean_df[col].dtype) if col in clean_df.columns else "УДАЛЕН"
        dtype_str = f"{orig_dtype:<10} -> {clean_dtype:<10}"
        
        orig_nulls = int(original_df[col].isna().sum())
        clean_nulls = int(clean_df[col].isna().sum()) if col in clean_df.columns else "N/A"
        nulls_str = f"{orig_nulls:<5} -> {clean_nulls}"
        
        col_fmt = f"{str(col)[:20]:<20}"
        lines.append(f"{col_fmt} | {dtype_str} | {nulls_str}")
        
    return "\n".join(lines)


def _extract_bad_indices_from_errors(error_report: pd.DataFrame, df: pd.DataFrame) -> set:
    """
    Извлекает индексы битых строк из failure_cases.
    Обрабатывает случаи, когда индекс отсутствует или записан в текстовом виде ошибки.
    """
    bad_indices = set()
    
    for _, row in error_report.iterrows():
        idx = row.get('index')
        
        # Если индекс есть и не NaN
        if pd.notna(idx):
            if isinstance(idx, (list, pd.Series, np.ndarray)):
                bad_indices.update(idx)
            else:
                bad_indices.add(idx)
        else:
            # Если индекса нет, пытаемся извлечь его из текстового представления ошибки
            error_msg = str(row.get('error', ''))
            
            # Паттерн для поиска индексов в сообщениях об ошибках coerce_dtype
            # Пример: "index failure_case0   1500       BAD_ID"
            matches = re.findall(r'index\s+failure_case\d+\s+(\d+)', error_msg)
            if matches:
                bad_indices.update(int(m) for m in matches)
            
            # Паттерн для поиска индексов в сообщениях о null values
            # Пример: "contains null values:15     NaT72     NaT"
            matches = re.findall(r'(\d+)\s+(?:NaT|NaN|None)', error_msg)
            if matches:
                bad_indices.update(int(m) for m in matches)
    
    return bad_indices


def validate_and_quarantine(df: pd.DataFrame, schema: pa.DataFrameModel) -> ValidationResult:
    """
    Проводит валидацию, разделяет данные и автоматически применяет типы из схемы.
    """
    df_name = df.attrs.get("name", "Без названия")
    try:
        validated_df = schema.validate(df, lazy=True)
        
        comparison_report = _build_comparison_report(df, validated_df)
        
        summary = (
            f"Отчёт по данным: {df_name}:\n"
            f"✅ ВАЛИДАЦИЯ ПРОШЛА УСПЕШНО\n"
            f"{'='*78}\n"
            f"📊 Статистика строк:\n"
            f"   • Исходный датасет:  {len(df):>6}\n"
            f"   • Очищенный датасет: {len(validated_df):>6} (100.0%)\n"
            f"   • Карантин:               0\n\n"
            f"📋 Сравнение состояния данных (Исходный -> Очищенный):\n"
            f"{comparison_report}"
        )
        
        return ValidationResult(
            is_valid=True,
            clean_df=validated_df,
            quarantine_df=pd.DataFrame(),
            error_report=pd.DataFrame(),
            summary=summary
        )
        
    except pa.errors.SchemaErrors as e:
        error_report = e.failure_cases
        
        bad_indices = _extract_bad_indices_from_errors(error_report, df)
        bad_indices = list(bad_indices)
        
        if bad_indices:
            quarantine_df = df.loc[bad_indices].copy()
            clean_df = df.drop(index=bad_indices).copy()
        else:
            quarantine_df = df.copy()
            clean_df = df.iloc[0:0].copy()
        
        # ВАЖНО: Применяем типы из схемы к чистым данным
        clean_df = _apply_schema_types_to_df(clean_df, schema)
        
        unique_errors = error_report[['column', 'check', 'failure_case']].drop_duplicates()
        errors_str = unique_errors.to_string(index=False) if not unique_errors.empty else "Нет специфичных ошибок"
        
        comparison_report = _build_comparison_report(df, clean_df)
        
        clean_pct = (len(clean_df) / len(df) * 100) if len(df) > 0 else 0.0
        
        summary = (
            f"Отчёт по данным: {df_name}:\n"
            f"❌ ОБНАРУЖЕНЫ ОШИБКИ ВАЛИДАЦИИ\n"
            f"{'='*78}\n"
            f"📊 Статистика строк:\n"
            f"   • Исходный датасет:  {len(df):>6}\n"
            f"   • Очищенный датасет: {len(clean_df):>6} ({clean_pct:>5.1f}%)\n"
            f"   • Карантин (ошибки): {len(quarantine_df):>6}\n\n"
            f"📋 Сравнение состояния данных (Исходный -> Очищенный):\n"
            f"{comparison_report}\n\n"
            f"🚨 Детали ошибок валидации (отправленных в карантин):\n"
            f"{errors_str}"
        )
        
        return ValidationResult(
            is_valid=False,
            clean_df=clean_df,
            quarantine_df=quarantine_df,
            error_report=error_report,
            summary=summary
        )


def _apply_schema_types_to_df(df: pd.DataFrame, schema) -> pd.DataFrame:
    """Применяет типы данных из схемы Pandera к DataFrame"""
    df_clean = df.copy()
    
    if hasattr(schema, 'to_schema'):
        pandera_schema = schema.to_schema()
    else:
        pandera_schema = schema
    
    for col_name, col_schema in pandera_schema.columns.items():
        if col_name not in df_clean.columns:
            continue
        
        expected_dtype = col_schema.dtype.type
        
        try:
            if expected_dtype == np.int64 or expected_dtype == int:
                df_clean[col_name] = pd.to_numeric(df_clean[col_name], errors='coerce').astype('Int64')
            elif expected_dtype == np.float64 or expected_dtype == float:
                df_clean[col_name] = pd.to_numeric(df_clean[col_name], errors='coerce')
            elif expected_dtype == np.bool_ or expected_dtype == bool:
                df_clean[col_name] = df_clean[col_name].astype(bool)
            elif 'datetime' in str(expected_dtype):
                df_clean[col_name] = pd.to_datetime(df_clean[col_name], errors='coerce')
            elif expected_dtype == str or expected_dtype == np.str_:
                df_clean[col_name] = df_clean[col_name].astype(str)
        except Exception:
            pass
    
    return df_clean

