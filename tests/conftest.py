"""Shared pytest fixtures."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest
from httpx import ASGITransport, AsyncClient

from src.config import Settings
from src.services import ServiceContainer
from src.services.ai import AIService
from src.services.database import DatabaseService
from src.storage.report_store import ReportStore


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        reports_dir=tmp_path / "reports",
        uploads_dir=tmp_path / "uploads",
    )


@pytest.fixture
def mock_ai() -> AIService:
    ai = MagicMock(spec=AIService)
    ai.call_llm = AsyncMock(return_value=None)
    ai.has_providers = False
    return ai


@pytest.fixture
def container(settings: Settings, mock_ai: AIService) -> ServiceContainer:
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    return ServiceContainer(
        ai=mock_ai,
        db=DatabaseService(""),
        store=ReportStore(settings.reports_dir),
        settings=settings,
    )


@pytest.fixture
async def api_client(container: ServiceContainer):
    import src.app as app_module
    app_module._container = container
    from src.app import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    p = tmp_path / "sales.csv"
    p.write_text(
        "product,revenue,quantity\nWidget,100,5\nGadget,200,3\nWidget,150,7\n",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame({
        "product": ["Widget", "Gadget", "Widget"],
        "revenue": [100, 200, 150],
        "quantity": [5, 3, 7],
    })
