"""Tests for pipeline orchestrator (TDD — written before implementation)."""
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest

from src.models import ReportOptions, ReportRequest, ReportStatus, ReportType
from src.pipeline.processor import generate_report
from src.services import ServiceContainer
from src.services.ai import AIService
from src.services.database import DatabaseService
from src.storage.report_store import ReportStore


@pytest.fixture
def tmp_store(tmp_path):
    return ReportStore(tmp_path / "reports")


@pytest.fixture
def mock_ai():
    ai = MagicMock(spec=AIService)
    ai.call_llm = AsyncMock(return_value=None)  # no AI — use template fallback
    ai.has_providers = False
    return ai


@pytest.fixture
def container(tmp_path, mock_ai, tmp_store):
    from src.config import Settings
    settings = Settings(
        reports_dir=tmp_path / "reports",
        uploads_dir=tmp_path / "uploads",
    )
    return ServiceContainer(
        ai=mock_ai,
        db=DatabaseService(""),
        store=tmp_store,
        settings=settings,
    )


@pytest.fixture
def sales_df():
    return pd.DataFrame({
        "product": ["Widget", "Gadget", "Widget", "Gadget"],
        "revenue": [100, 200, 150, 250],
        "quantity": [5, 3, 7, 2],
    })


async def test_full_pipeline_csv(sales_df, container, tmp_path):
    request = ReportRequest(title="Sales Q1", report_type=ReportType.sales)
    result = await generate_report(sales_df, request, container)
    assert result.status == ReportStatus.completed
    assert result.title == "Sales Q1"
    assert result.data_summary is not None
    assert result.html_path is not None


async def test_pipeline_no_ai_uses_template(sales_df, container):
    request = ReportRequest(title="Test Report", report_type=ReportType.generic)
    result = await generate_report(sales_df, request, container)
    assert len(result.narrative_sections) >= 2


async def test_pipeline_pdf_skipped_when_unavailable(sales_df, container):
    request = ReportRequest(title="PDF Test", report_type=ReportType.generic)
    result = await generate_report(sales_df, request, container)
    # PDF is either None or a valid path — both acceptable
    assert result.pdf_path is None or Path(result.pdf_path).exists()


async def test_pipeline_tracks_stage_times(sales_df, container):
    request = ReportRequest(title="Timing Test", report_type=ReportType.generic)
    result = await generate_report(sales_df, request, container)
    assert result.processing_time_ms > 0
    assert "profile" in result.stage_times_ms
