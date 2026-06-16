import pandas as pd
import numpy as np
from pathlib import Path
import pandera as pa
import pandas as pd
from pandera.typing import Series
from dataclasses import dataclass
import phonenumbers
import re

@dataclass
class ValidationResult:
    is_valid: bool
    clean_df: pd.DataFrame
    quarantine_df: pd.DataFrame
    error_report: pd.DataFrame
    summary: str

def validate_and_quarantine(df: pd.DataFrame, schema: pa.DataFrameModel) -> ValidationResult:
    try:
        validated_df = schema.validate(df, lazy=True)
        
        return ValidationResult(
            is_valid=True,
            clean_df=validated_df,
            quarantine_df=pd.DataFrame(),
            error_report=pd.DataFrame(),
            summary=f"✅ Валидация прошла успешно! Все {len(df)} записей соответствуют формату."
        )
        
    except pa.errors.SchemaErrors as e:
        error_report = e.failure_cases
        
        bad_indices = set()
        for item in error_report['index']:
            if pd.isna(item):
                continue
            if isinstance(item, (list, pd.Series, np.ndarray)):
                bad_indices.update(item)
            else:
                bad_indices.add(item)
        
        bad_indices = list(bad_indices)
        
        quarantine_df = df.loc[bad_indices].copy()
        clean_df = df.drop(index=bad_indices).copy()
        
        unique_errors = error_report[['column', 'check', 'failure_case']].drop_duplicates()
        
        summary = (
            f"❌ Обнаружены ошибки валидации.\n"
            f"📊 Статистика:\n"
            f"   - Всего строк: {len(df)}\n"
            f"   - Чистых строк: {len(clean_df)} ({len(clean_df)/len(df)*100:.1f}%)\n"
            f"   - В карантине: {len(quarantine_df)}\n\n"
            f"📋 Детали ошибок:\n{unique_errors.to_string(index=False)}"
        )
        
        return ValidationResult(
            is_valid=False,
            clean_df=clean_df,
            quarantine_df=quarantine_df,
            error_report=error_report,
            summary=summary
        )