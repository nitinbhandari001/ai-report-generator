from typing import Any

from src.models import DataSummary, NarrativeSection, ReportType, SectionType

_EXEC_TEMPLATES: dict[ReportType, str] = {
    ReportType.sales: (
        "This sales report covers {rows} records across {cols} dimensions. "
        "Data quality score: {quality:.0f}/100."
    ),
    ReportType.financial: (
        "This financial report analyzes {rows} transactions across {cols} categories. "
        "Data quality: {quality:.0f}/100."
    ),
    ReportType.marketing: (
        "This marketing report summarizes {rows} campaign records. "
        "Quality score: {quality:.0f}/100."
    ),
    ReportType.hr: (
        "This HR report covers {rows} workforce records. "
        "Data completeness score: {quality:.0f}/100."
    ),
    ReportType.generic: (
        "This report analyzes {rows} records with {cols} data points. "
        "Quality score: {quality:.0f}/100."
    ),
    ReportType.auto: (
        "This report analyzes {rows} records with {cols} data points. "
        "Quality score: {quality:.0f}/100."
    ),
}

_FINDINGS_TEMPLATES: dict[ReportType, str] = {
    ReportType.sales: "Dataset contains {cols} columns. Key numeric metrics captured for analysis.",
    ReportType.financial: "Financial records include {cols} fields for comprehensive budget analysis.",
    ReportType.marketing: "Campaign data includes {cols} performance metrics for channel analysis.",
    ReportType.hr: "Workforce data includes {cols} attributes for organizational analysis.",
    ReportType.generic: "Dataset includes {cols} columns with {rows} data points for analysis.",
    ReportType.auto: "Dataset includes {cols} columns with {rows} data points for analysis.",
}


def render_template_narrative(
    report_type: ReportType,
    summary: DataSummary,
    stats: dict[str, Any],
) -> list[NarrativeSection]:
    ctx = {
        "rows": summary.row_count,
        "cols": summary.column_count,
        "quality": summary.quality_score,
    }
    rtype = report_type if report_type in _EXEC_TEMPLATES else ReportType.generic
    exec_tmpl = _EXEC_TEMPLATES.get(rtype, _EXEC_TEMPLATES[ReportType.generic])
    findings_tmpl = _FINDINGS_TEMPLATES.get(rtype, _FINDINGS_TEMPLATES[ReportType.generic])

    sections = [
        NarrativeSection(
            section_type=SectionType.executive_summary,
            content=exec_tmpl.format(**ctx),
            confidence=0.7,
        ),
        NarrativeSection(
            section_type=SectionType.key_findings,
            content=findings_tmpl.format(**ctx),
            confidence=0.7,
        ),
    ]

    # Trends from stats
    trends = stats.get("trends", {})
    if trends:
        trend_lines = [f"{col}: {direction}" for col, direction in trends.items()]
        sections.append(NarrativeSection(
            section_type=SectionType.trends,
            content="Observed trends: " + "; ".join(trend_lines) + ".",
            confidence=0.65,
        ))

    # Recommendations
    sections.append(NarrativeSection(
        section_type=SectionType.recommendations,
        content=(
            "Review data quality metrics and address any null values. "
            "Consider drill-down analysis on high-variance columns."
        ),
        confidence=0.6,
    ))

    return sections
