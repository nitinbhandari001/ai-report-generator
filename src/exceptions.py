class ReportError(Exception):
    """Base exception for ai-report-generator."""


class IngestionError(ReportError):
    """Failed to load/parse input data."""


class AnalysisError(ReportError):
    """Failed during data analysis/profiling."""


class ChartError(ReportError):
    """Failed during chart generation."""


class NarrativeError(ReportError):
    """Failed during AI narrative generation."""


class RenderError(ReportError):
    """Failed during HTML/PDF rendering."""


class ReportNotFoundError(ReportError):
    """Report ID not found in store."""


class DatabaseError(ReportError):
    """Failed during database query execution."""
