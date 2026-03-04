from __future__ import annotations

from dataclasses import dataclass

from src.config import Settings
from src.services.ai import AIService
from src.services.database import DatabaseService
from src.storage.report_store import ReportStore


@dataclass
class ServiceContainer:
    ai: AIService
    db: DatabaseService
    store: ReportStore
    settings: Settings


async def create_services(settings: Settings) -> ServiceContainer:
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    return ServiceContainer(
        ai=AIService.from_settings(settings),
        db=DatabaseService(settings.database_url),
        store=ReportStore(settings.reports_dir),
        settings=settings,
    )
