"""Tests for narrative generation (TDD — written before implementation)."""
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest

from src.models import DataSummary, NarrativeSection, ReportType, SectionType
from src.narrative.templates import render_template_narrative
from src.narrative.writer import generate_narrative


@pytest.fixture
def empty_summary() -> DataSummary:
    return DataSummary(row_count=0, column_count=0, columns=[])


@pytest.fixture
def sales_summary() -> DataSummary:
    from src.models import ColumnProfile
    return DataSummary(
        row_count=100,
        column_count=3,
        columns=[
            ColumnProfile(name="revenue", dtype="float64", null_count=0, null_pct=0.0,
                          unique_count=80, mean=500.0, median=450.0, std=120.0),
        ],
        quality_score=95.0,
    )


def test_template_fallback_when_no_ai(sales_summary):
    sections = render_template_narrative(ReportType.sales, sales_summary, {})
    assert len(sections) >= 2
    assert any(s.section_type == SectionType.executive_summary for s in sections)


async def test_ai_narrative_parsed(sales_summary):
    import json
    mock_ai = MagicMock()
    mock_ai.call_llm = AsyncMock(return_value=json.dumps([
        {"section_type": "executive_summary", "content": "Strong performance.", "confidence": 0.9},
        {"section_type": "key_findings", "content": "Revenue up 20%.", "confidence": 0.85},
    ]))
    sections = await generate_narrative(mock_ai, sales_summary, {}, ReportType.sales)
    assert len(sections) == 2
    assert sections[0].section_type == SectionType.executive_summary


async def test_narrative_has_all_section_types(sales_summary):
    sections = render_template_narrative(ReportType.generic, sales_summary, {})
    types = {s.section_type for s in sections}
    assert SectionType.executive_summary in types
    assert SectionType.key_findings in types


async def test_empty_data_handled(empty_summary):
    sections = render_template_narrative(ReportType.generic, empty_summary, {})
    assert isinstance(sections, list)
