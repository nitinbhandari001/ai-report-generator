import asyncio
from typing import Any

import pandas as pd

from src.models import ColumnProfile, DataSummary


def _profile(df: pd.DataFrame) -> DataSummary:
    columns: list[ColumnProfile] = []
    null_pct_sum = 0.0
    total = len(df)

    for col_name in df.columns:
        series = df[col_name]
        null_count = int(series.isna().sum())
        null_pct = (null_count / total * 100) if total else 0.0
        null_pct_sum += null_pct
        unique_count = int(series.nunique(dropna=True))
        dtype = str(series.dtype)

        mean = median = std = None
        min_val: Any = None
        max_val: Any = None
        top_values: list[Any] = []

        if pd.api.types.is_numeric_dtype(series):
            clean = series.dropna()
            if len(clean):
                mean = float(clean.mean())
                median = float(clean.median())
                std = float(clean.std()) if len(clean) > 1 else 0.0
                min_val = float(clean.min())
                max_val = float(clean.max())
        else:
            vc = series.value_counts().head(5)
            top_values = [{"value": k, "count": int(v)} for k, v in vc.items()]
            if len(series.dropna()):
                min_val = str(series.dropna().iloc[0])
                max_val = str(series.dropna().iloc[-1])

        columns.append(ColumnProfile(
            name=col_name,
            dtype=dtype,
            null_count=null_count,
            null_pct=round(null_pct, 2),
            unique_count=unique_count,
            min=min_val,
            max=max_val,
            mean=mean,
            median=median,
            std=std,
            top_values=top_values,
        ))

    # Quality score
    avg_null_pct = null_pct_sum / len(df.columns) if df.columns.size else 0.0
    dup_pct = (df.duplicated().sum() / total * 100) if total else 0.0
    quality_score = max(0.0, 100.0 - avg_null_pct * 0.5 - dup_pct * 0.3)

    # Date range
    date_range = None
    for col_name in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col_name]):
            clean = df[col_name].dropna()
            if len(clean):
                date_range = {
                    "start": str(clean.min().date()),
                    "end": str(clean.max().date()),
                }
            break

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(exclude="number").columns.tolist()

    return DataSummary(
        row_count=total,
        column_count=len(df.columns),
        columns=columns,
        date_range=date_range,
        numeric_summary={"numeric_columns": numeric_cols},
        categorical_summary={"categorical_columns": cat_cols},
        quality_score=round(quality_score, 1),
    )


async def profile_dataframe(df: pd.DataFrame) -> DataSummary:
    return await asyncio.to_thread(_profile, df)
