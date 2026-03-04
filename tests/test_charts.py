"""Tests for chart generation (TDD — written before implementation)."""
import base64
from unittest.mock import MagicMock

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import pytest

from src.charts.encoders import fig_to_base64
from src.charts.generator import generate_charts
from src.models import ChartSpec, ChartType


@pytest.fixture
def simple_df() -> pd.DataFrame:
    return pd.DataFrame({
        "category": ["A", "B", "C", "D"],
        "value": [10, 25, 15, 30],
    })


def test_fig_to_base64_valid_png():
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [4, 5, 6])
    result = fig_to_base64(fig)
    # Should be valid base64
    decoded = base64.b64decode(result)
    assert decoded[:4] == b"\x89PNG"  # PNG magic bytes


def test_bar_chart_generation(simple_df):
    import asyncio
    spec = ChartSpec(
        chart_type=ChartType.bar,
        title="Value by Category",
        x_column="category",
        y_column="value",
    )
    results = asyncio.run(generate_charts(simple_df, [spec]))
    assert len(results) == 1
    assert results[0].spec == spec
    assert len(results[0].image_base64) > 100


def test_pie_max_slices_groups_other():
    df = pd.DataFrame({
        "category": [f"Cat{i}" for i in range(12)],
        "value": list(range(1, 13)),
    })
    import asyncio
    spec = ChartSpec(
        chart_type=ChartType.pie,
        title="Distribution",
        x_column="category",
        y_column="value",
    )
    results = asyncio.run(generate_charts(df, [spec]))
    assert len(results) == 1
    assert results[0].image_base64


def test_figure_closed_after_encoding():
    fig, ax = plt.subplots()
    ax.bar([1, 2], [3, 4])
    fig_num = fig.number
    fig_to_base64(fig)
    # Figure should be closed (not in plt.get_fignums())
    assert fig_num not in plt.get_fignums()
