from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict


# ── Enums ────────────────────────────────────────────────────────────────────

class ReportStatus(StrEnum):
    pending = "pending"
    ingesting = "ingesting"
    analyzing = "analyzing"
    charting = "charting"
    narrating = "narrating"
    rendering = "rendering"
    completed = "completed"
    failed = "failed"


class ReportType(StrEnum):
    sales = "sales"
    financial = "financial"
    marketing = "marketing"
    hr = "hr"
    generic = "generic"
    auto = "auto"


class ChartType(StrEnum):
    bar = "bar"
    line = "line"
    pie = "pie"
    hbar = "hbar"
    grouped_bar = "grouped_bar"
    scatter = "scatter"


class SectionType(StrEnum):
    executive_summary = "executive_summary"
    key_findings = "key_findings"
    trends = "trends"
    recommendations = "recommendations"


# ── Analysis models ──────────────────────────────────────────────────────────

class ColumnProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    dtype: str
    null_count: int
    null_pct: float
    unique_count: int
    min: float | str | None = None
    max: float | str | None = None
    mean: float | None = None
    median: float | None = None
    std: float | None = None
    top_values: list[Any] = []


class DataSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    row_count: int
    column_count: int
    columns: list[ColumnProfile]
    date_range: dict[str, str] | None = None
    numeric_summary: dict[str, Any] = {}
    categorical_summary: dict[str, Any] = {}
    quality_score: float = 100.0


# ── Chart models ─────────────────────────────────────────────────────────────

class ChartSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    chart_type: ChartType
    title: str
    x_column: str
    y_column: str | None = None
    y_columns: list[str] = []


class ChartResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    spec: ChartSpec
    image_base64: str


# ── Narrative models ─────────────────────────────────────────────────────────

class NarrativeSection(BaseModel):
    model_config = ConfigDict(frozen=True)

    section_type: SectionType
    content: str
    confidence: float = 1.0


# ── Request / result models ──────────────────────────────────────────────────

class ReportOptions(BaseModel):
    model_config = ConfigDict(frozen=True)

    include_charts: bool = True
    include_narrative: bool = True
    include_raw_data: bool = False
    max_charts: int = 6
    color_palette: str = "professional"
    page_size: str = "A4"


class ReportRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    report_type: ReportType = ReportType.auto
    options: ReportOptions = ReportOptions()
    chart_specs: list[ChartSpec] | None = None


class ReportResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    report_id: str
    status: ReportStatus
    title: str
    report_type: ReportType
    created_at: datetime
    data_summary: DataSummary | None = None
    charts: list[ChartResult] = []
    narrative_sections: list[NarrativeSection] = []
    html_path: str | None = None
    pdf_path: str | None = None
    processing_time_ms: int = 0
    stage_times_ms: dict[str, int] = {}
    error: str | None = None
