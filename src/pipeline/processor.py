from __future__ import annotations

import time
import uuid
from datetime import datetime

import pandas as pd
import structlog

from src.analysis.detector import detect_report_type, recommend_charts
from src.analysis.profiler import profile_dataframe
from src.analysis.statistics import compute_statistics
from src.charts.generator import generate_charts
from src.models import (
    ReportRequest, ReportResult, ReportStatus, ReportType,
)
from src.narrative.writer import generate_narrative
from src.renderer.html_renderer import render_html
from src.renderer.pdf_renderer import render_pdf
from src.services import ServiceContainer

log = structlog.get_logger(__name__)


async def generate_report(
    df: pd.DataFrame,
    request: ReportRequest,
    container: ServiceContainer,
) -> ReportResult:
    report_id = str(uuid.uuid4())
    started_at = time.monotonic()
    stage_times: dict[str, int] = {}
    settings = container.settings

    # Resolve report type
    resolved_type = request.report_type

    # Helper: time a stage
    def _t(name: str, t0: float) -> None:
        stage_times[name] = int((time.monotonic() - t0) * 1000)

    # ── Stage: profile ──────────────────────────────────────────────────────
    t0 = time.monotonic()
    try:
        summary = await profile_dataframe(df)
    except Exception as exc:
        log.error("profile_failed", error=str(exc))
        return ReportResult(
            report_id=report_id,
            status=ReportStatus.failed,
            title=request.title,
            report_type=resolved_type,
            created_at=datetime.now(),
            error=str(exc),
        )
    _t("profile", t0)

    # ── Stage: statistics ────────────────────────────────────────────────────
    t0 = time.monotonic()
    try:
        stats = await compute_statistics(df, summary)
    except Exception as exc:
        log.warning("stats_failed", error=str(exc))
        stats = {}
    _t("statistics", t0)

    # ── Stage: detect type ───────────────────────────────────────────────────
    if resolved_type == ReportType.auto:
        resolved_type = detect_report_type(df, summary)

    # ── Stage: charts ────────────────────────────────────────────────────────
    t0 = time.monotonic()
    charts = []
    if request.options.include_charts:
        specs = request.chart_specs or recommend_charts(
            df, summary, resolved_type, request.options.max_charts
        )
        try:
            charts = await generate_charts(df, specs, request.options.color_palette)
        except Exception as exc:
            log.warning("charts_failed", error=str(exc))
    _t("charts", t0)

    # ── Stage: narrative ─────────────────────────────────────────────────────
    t0 = time.monotonic()
    narrative_sections = []
    if request.options.include_narrative:
        try:
            narrative_sections = await generate_narrative(
                container.ai, summary, stats, resolved_type
            )
        except Exception as exc:
            log.warning("narrative_failed", error=str(exc))
    _t("narrative", t0)

    # Build partial result for rendering
    partial = ReportResult(
        report_id=report_id,
        status=ReportStatus.rendering,
        title=request.title,
        report_type=resolved_type,
        created_at=datetime.now(),
        data_summary=summary,
        charts=charts,
        narrative_sections=narrative_sections,
        stage_times_ms=stage_times,
    )

    # ── Stage: render HTML ────────────────────────────────────────────────────
    t0 = time.monotonic()
    html_path = None
    try:
        html_path = await render_html(partial, resolved_type, settings.reports_dir)
    except Exception as exc:
        log.warning("html_render_failed", error=str(exc))
    _t("render_html", t0)

    # ── Stage: render PDF ─────────────────────────────────────────────────────
    t0 = time.monotonic()
    pdf_path = None
    if html_path:
        try:
            pdf_path = await render_pdf(html_path)
        except Exception as exc:
            log.warning("pdf_render_failed", error=str(exc))
    _t("render_pdf", t0)

    total_ms = int((time.monotonic() - started_at) * 1000)
    stage_times["total"] = total_ms

    result = ReportResult(
        report_id=report_id,
        status=ReportStatus.completed,
        title=request.title,
        report_type=resolved_type,
        created_at=partial.created_at,
        data_summary=summary,
        charts=charts,
        narrative_sections=narrative_sections,
        html_path=str(html_path) if html_path else None,
        pdf_path=str(pdf_path) if pdf_path else None,
        processing_time_ms=total_ms,
        stage_times_ms=stage_times,
    )

    await container.store.save_report(result)
    log.info("report_generated", report_id=report_id, ms=total_ms)
    return result
