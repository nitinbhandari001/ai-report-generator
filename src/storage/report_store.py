from __future__ import annotations

import asyncio
import json
from pathlib import Path

import structlog

from src.exceptions import ReportNotFoundError
from src.models import ReportResult

log = structlog.get_logger(__name__)


class ReportStore:
    def __init__(self, reports_dir: Path) -> None:
        self._dir = reports_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, ReportResult] = {}
        self._lock = asyncio.Lock()

    def _index_path(self) -> Path:
        return self._dir / "_index.json"

    def _load_index(self) -> None:
        idx = self._index_path()
        if idx.exists():
            data = json.loads(idx.read_text(encoding="utf-8"))
            for report_id, raw in data.items():
                if report_id not in self._cache:
                    self._cache[report_id] = ReportResult.model_validate(raw)

    def _save_index(self) -> None:
        data = {rid: r.model_dump(mode="json") for rid, r in self._cache.items()}
        self._index_path().write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    async def save_report(self, result: ReportResult) -> None:
        async with self._lock:
            self._cache[result.report_id] = result
            await asyncio.to_thread(self._save_index)

    async def get_report(self, report_id: str) -> ReportResult:
        async with self._lock:
            if report_id not in self._cache:
                await asyncio.to_thread(self._load_index)
            if report_id not in self._cache:
                raise ReportNotFoundError(f"Report not found: {report_id}")
            return self._cache[report_id]

    async def list_reports(self) -> list[ReportResult]:
        async with self._lock:
            await asyncio.to_thread(self._load_index)
            return list(self._cache.values())

    async def delete_report(self, report_id: str) -> None:
        async with self._lock:
            if report_id not in self._cache:
                raise ReportNotFoundError(f"Report not found: {report_id}")
            result = self._cache.pop(report_id)
            # Delete associated files
            for path_str in [result.html_path, result.pdf_path]:
                if path_str:
                    p = Path(path_str)
                    if p.exists():
                        p.unlink(missing_ok=True)
            await asyncio.to_thread(self._save_index)
