import asyncio
from typing import Any

import numpy as np
import pandas as pd

from src.models import DataSummary


def _compute(df: pd.DataFrame, summary: DataSummary) -> dict[str, Any]:
    result: dict[str, Any] = {}
    numeric = df.select_dtypes(include="number")

    # Correlation matrix
    correlations: list[dict] = []
    if len(numeric.columns) >= 2:
        corr = numeric.corr()
        cols = corr.columns.tolist()
        for i, c1 in enumerate(cols):
            for j, c2 in enumerate(cols):
                if i < j:
                    val = corr.iloc[i, j]
                    if abs(val) > 0.7:
                        correlations.append({"col_a": c1, "col_b": c2, "r": round(float(val), 3)})
    result["correlations"] = correlations

    # Outliers (IQR)
    outliers: dict[str, int] = {}
    for col in numeric.columns:
        s = numeric[col].dropna()
        if len(s) < 4:
            continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        n_out = int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum())
        if n_out:
            outliers[col] = n_out
    result["outliers"] = outliers

    # Trends (date column)
    trends: dict[str, str] = {}
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            x = np.arange(len(df))
            for num_col in numeric.columns:
                y = df[num_col].ffill().values
                if len(y) < 2:
                    continue
                slope = float(np.polyfit(x, y, 1)[0])
                if slope > 0.01:
                    trends[num_col] = "increasing"
                elif slope < -0.01:
                    trends[num_col] = "decreasing"
                else:
                    trends[num_col] = "stable"
            break
    result["trends"] = trends

    # Top-N categorical
    top_categorical: dict[str, list] = {}
    for col in df.select_dtypes(exclude="number").columns:
        vc = df[col].value_counts().head(5)
        top_categorical[col] = [{"value": k, "count": int(v)} for k, v in vc.items()]
    result["top_categorical"] = top_categorical

    return result


async def compute_statistics(df: pd.DataFrame, summary: DataSummary) -> dict[str, Any]:
    return await asyncio.to_thread(_compute, df, summary)
