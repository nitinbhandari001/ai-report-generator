import asyncio
import logging
from pathlib import Path

import structlog

log = structlog.get_logger(__name__)

_PDF_AVAILABLE: bool | None = None


def _check_pdf() -> bool:
    global _PDF_AVAILABLE
    if _PDF_AVAILABLE is None:
        try:
            from weasyprint import HTML  # noqa: F401
            _PDF_AVAILABLE = True
        except Exception:
            _PDF_AVAILABLE = False
    return _PDF_AVAILABLE


def _write_pdf(html_path: Path) -> Path:
    from weasyprint import HTML
    pdf_path = html_path.with_suffix(".pdf")
    HTML(filename=str(html_path)).write_pdf(str(pdf_path))
    return pdf_path


async def render_pdf(html_path: Path) -> Path | None:
    if not _check_pdf():
        log.warning("weasyprint_unavailable", hint="Install with: pip install weasyprint")
        return None
    try:
        return await asyncio.to_thread(_write_pdf, html_path)
    except Exception as exc:
        log.warning("pdf_render_failed", error=str(exc))
        return None
