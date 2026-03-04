import asyncio

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from src.charts.encoders import fig_to_base64
from src.charts.palette import get_palette
from src.models import ChartResult, ChartSpec, ChartType

matplotlib.use("Agg")

_MAX_PIE_SLICES = 8


def _apply_style(ax, title: str) -> None:
    ax.set_title(title, fontsize=13, fontweight="bold", fontfamily="sans-serif", pad=10)
    ax.grid(True, linestyle="--", alpha=0.4)
    for spine in ax.spines.values():
        spine.set_visible(False)


def _render_bar(df: pd.DataFrame, spec: ChartSpec, colors: list[str]) -> Figure:
    data = df.groupby(spec.x_column)[spec.y_column].sum()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(data.index, data.values, color=colors[: len(data)])
    ax.set_xlabel(spec.x_column)
    ax.set_ylabel(spec.y_column or "")
    _apply_style(ax, spec.title)
    plt.xticks(rotation=30, ha="right")
    fig.tight_layout()
    return fig


def _render_line(df: pd.DataFrame, spec: ChartSpec, colors: list[str]) -> Figure:
    fig, ax = plt.subplots(figsize=(8, 5))
    cols = spec.y_columns if spec.y_columns else ([spec.y_column] if spec.y_column else [])
    for i, col in enumerate(cols):
        ax.plot(df[spec.x_column], df[col], marker="o", label=col, color=colors[i % len(colors)])
    ax.set_xlabel(spec.x_column)
    _apply_style(ax, spec.title)
    if len(cols) > 1:
        ax.legend()
    plt.xticks(rotation=30, ha="right")
    fig.tight_layout()
    return fig


def _render_pie(df: pd.DataFrame, spec: ChartSpec, colors: list[str]) -> Figure:
    data = df.groupby(spec.x_column)[spec.y_column].sum().sort_values(ascending=False)
    if len(data) > _MAX_PIE_SLICES:
        top = data.head(_MAX_PIE_SLICES - 1)
        other = pd.Series({"Other": data.iloc[_MAX_PIE_SLICES - 1 :].sum()})
        data = pd.concat([top, other])
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(data.values, labels=data.index, colors=colors[: len(data)], autopct="%1.1f%%", startangle=90)
    ax.set_title(spec.title, fontsize=13, fontweight="bold", fontfamily="sans-serif")
    fig.tight_layout()
    return fig


def _render_hbar(df: pd.DataFrame, spec: ChartSpec, colors: list[str]) -> Figure:
    data = df.groupby(spec.x_column)[spec.y_column].sum().sort_values()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(data.index, data.values, color=colors[: len(data)])
    ax.set_xlabel(spec.y_column or "")
    _apply_style(ax, spec.title)
    fig.tight_layout()
    return fig


def _render_scatter(df: pd.DataFrame, spec: ChartSpec, colors: list[str]) -> Figure:
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(df[spec.x_column], df[spec.y_column], color=colors[0], alpha=0.7)
    ax.set_xlabel(spec.x_column)
    ax.set_ylabel(spec.y_column or "")
    _apply_style(ax, spec.title)
    fig.tight_layout()
    return fig


_RENDERERS = {
    ChartType.bar: _render_bar,
    ChartType.line: _render_line,
    ChartType.pie: _render_pie,
    ChartType.hbar: _render_hbar,
    ChartType.grouped_bar: _render_bar,  # fallback to bar
    ChartType.scatter: _render_scatter,
}


def _generate_all(df: pd.DataFrame, specs: list[ChartSpec], palette: str) -> list[ChartResult]:
    colors = get_palette(palette)
    results = []
    for spec in specs:
        renderer = _RENDERERS.get(spec.chart_type, _render_bar)
        try:
            fig = renderer(df, spec, colors)
            image_b64 = fig_to_base64(fig)
            results.append(ChartResult(spec=spec, image_base64=image_b64))
        except Exception:
            pass
    return results


async def generate_charts(
    df: pd.DataFrame,
    specs: list[ChartSpec],
    palette: str = "professional",
) -> list[ChartResult]:
    return await asyncio.to_thread(_generate_all, df, specs, palette)
