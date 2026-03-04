"""Tests for analysis layer (TDD — written before implementation)."""
import pandas as pd
import pytest

from src.analysis.detector import detect_report_type, recommend_charts
from src.analysis.profiler import profile_dataframe
from src.analysis.statistics import compute_statistics
from src.models import ReportType


@pytest.fixture
def numeric_df() -> pd.DataFrame:
    return pd.DataFrame({
        "value": [10.0, 20.0, 30.0, 40.0, 50.0],
        "count": [1, 2, 3, 4, 5],
    })


@pytest.fixture
def categorical_df() -> pd.DataFrame:
    return pd.DataFrame({
        "category": ["A", "B", "A", "C", "B", "A"],
        "label": ["x", "y", "x", "y", "x", "y"],
    })


@pytest.fixture
def sales_df() -> pd.DataFrame:
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=6, freq="ME"),
        "product": ["Widget", "Gadget"] * 3,
        "revenue": [100, 200, 150, 250, 130, 220],
        "sales": [10, 20, 15, 25, 13, 22],
    })


async def test_profile_numeric_columns(numeric_df):
    summary = await profile_dataframe(numeric_df)
    assert summary.row_count == 5
    assert summary.column_count == 2
    col = next(c for c in summary.columns if c.name == "value")
    assert col.mean == pytest.approx(30.0)
    assert col.null_count == 0


async def test_profile_categorical_columns(categorical_df):
    summary = await profile_dataframe(categorical_df)
    col = next(c for c in summary.columns if c.name == "category")
    assert col.unique_count == 3
    assert len(col.top_values) > 0


async def test_correlation_detection(numeric_df):
    stats = await compute_statistics(numeric_df, await profile_dataframe(numeric_df))
    assert "correlations" in stats


async def test_trend_detection_with_dates(sales_df):
    summary = await profile_dataframe(sales_df)
    stats = await compute_statistics(sales_df, summary)
    assert "trends" in stats


async def test_detect_report_type_sales(sales_df):
    summary = await profile_dataframe(sales_df)
    report_type = detect_report_type(sales_df, summary)
    assert report_type == ReportType.sales
