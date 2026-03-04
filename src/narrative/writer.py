from __future__ import annotations

import json
import logging
from typing import Any

import structlog

from src.models import DataSummary, NarrativeSection, ReportType, SectionType
from src.narrative.templates import render_template_narrative
from src.services.ai import AIService

log = structlog.get_logger(__name__)

_SYSTEM_PROMPT = (
    "You are a senior business analyst. Write concise, insight-driven, actionable narrative. "
    "Return ONLY a JSON array of objects with keys: section_type, content, confidence. "
    "section_type must be one of: executive_summary, key_findings, trends, recommendations."
)

_VALID_TYPES = {st.value for st in SectionType}


def _build_user_prompt(summary: DataSummary, stats: dict, report_type: ReportType) -> str:
    numeric_cols = [c for c in summary.columns if c.mean is not None]
    col_info = [
        f"{c.name} (mean={c.mean:.1f}, std={c.std:.1f})"
        for c in numeric_cols[:8]
        if c.mean is not None and c.std is not None
    ]
    trends = stats.get("trends", {})
    correlations = stats.get("correlations", [])

    return (
        f"Report type: {report_type}\n"
        f"Rows: {summary.row_count}, Columns: {summary.column_count}\n"
        f"Quality score: {summary.quality_score}/100\n"
        f"Key numeric columns: {', '.join(col_info) or 'none'}\n"
        f"Trends: {json.dumps(trends)}\n"
        f"Correlations: {json.dumps(correlations[:5])}\n"
        "Write 4 narrative sections as a JSON array."
    )


async def generate_narrative(
    ai: AIService,
    summary: DataSummary,
    stats: dict[str, Any],
    report_type: ReportType,
) -> list[NarrativeSection]:
    user_prompt = _build_user_prompt(summary, stats, report_type)
    raw = await ai.call_llm(_SYSTEM_PROMPT, user_prompt)

    if raw:
        try:
            # Strip markdown code fences if present
            text = raw.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text.strip())
            sections = []
            for item in data:
                st = item.get("section_type", "")
                if st not in _VALID_TYPES:
                    continue
                sections.append(NarrativeSection(
                    section_type=SectionType(st),
                    content=str(item.get("content", "")),
                    confidence=float(item.get("confidence", 0.8)),
                ))
            if sections:
                return sections
        except Exception as exc:
            log.warning("narrative_parse_failed", error=str(exc))

    return render_template_narrative(report_type, summary, stats)
