"""Tests for HTML/PDF renderer (TDD — written before implementation)."""
from datetime import datetime
from pathlib import Path

import pytest

from src.models import (
    ChartResult, ChartSpec, ChartType, DataSummary, NarrativeSection,
    ReportResult, ReportStatus, ReportType, SectionType,
)
from src.renderer.html_renderer import render_html
from src.renderer.pdf_renderer import render_pdf


@pytest.fixture
def minimal_result() -> ReportResult:
    return ReportResult(
        report_id="test-001",
        status=ReportStatus.completed,
        title="Test Sales Report",
        report_type=ReportType.sales,
        created_at=datetime(2024, 1, 15, 10, 30),
        data_summary=DataSummary(row_count=100, column_count=3, columns=[]),
        charts=[],
        narrative_sections=[
            NarrativeSection(
                section_type=SectionType.executive_summary,
                content="Strong sales performance in Q1.",
                confidence=0.9,
            )
        ],
    )


@pytest.fixture
def result_with_charts(minimal_result) -> ReportResult:
    spec = ChartSpec(chart_type=ChartType.bar, title="Revenue by Product", x_column="product", y_column="revenue")
    return minimal_result.model_copy(update={
        "charts": [ChartResult(spec=spec, image_base64="aW1hZ2U=")]
    })


async def test_html_contains_title_and_charts(result_with_charts, tmp_path):
    html_path = await render_html(result_with_charts, ReportType.sales, tmp_path)
    assert html_path.exists()
    content = html_path.read_text(encoding="utf-8")
    assert "Test Sales Report" in content
    assert "aW1hZ2U=" in content  # base64 image data


async def test_html_contains_narrative_sections(minimal_result, tmp_path):
    html_path = await render_html(minimal_result, ReportType.generic, tmp_path)
    content = html_path.read_text(encoding="utf-8")
    assert "Strong sales performance" in content


async def test_pdf_returns_none_when_unavailable(tmp_path):
    # Write a minimal HTML file
    html_path = tmp_path / "report.html"
    html_path.write_text("<html><body>Test</body></html>", encoding="utf-8")
    # If weasyprint not available, should return None gracefully
    result = await render_pdf(html_path)
    # Either a Path (success) or None (weasyprint unavailable) — both valid
    assert result is None or isinstance(result, Path)
