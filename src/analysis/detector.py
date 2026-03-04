import pandas as pd

from src.models import ChartSpec, ChartType, DataSummary, ReportType

_KEYWORDS: dict[ReportType, list[str]] = {
    ReportType.sales: ["revenue", "sales", "product", "order", "quantity", "price", "discount"],
    ReportType.financial: ["income", "expense", "profit", "loss", "budget", "cost", "debit", "credit"],
    ReportType.marketing: ["campaign", "impressions", "clicks", "conversion", "spend", "ctr", "roas"],
    ReportType.hr: ["headcount", "turnover", "satisfaction", "tenure", "employee", "department", "hire"],
}


def detect_report_type(df: pd.DataFrame, summary: DataSummary) -> ReportType:
    col_names = " ".join(df.columns.str.lower())
    scores: dict[ReportType, int] = {t: 0 for t in _KEYWORDS}
    for rtype, kws in _KEYWORDS.items():
        for kw in kws:
            if kw in col_names:
                scores[rtype] += 1
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else ReportType.generic


def recommend_charts(
    df: pd.DataFrame,
    summary: DataSummary,
    report_type: ReportType,
    max_charts: int = 6,
) -> list[ChartSpec]:
    specs: list[ChartSpec] = []
    numeric_cols = [c.name for c in summary.columns if c.mean is not None]
    cat_cols = [c.name for c in summary.columns if c.mean is None and c.unique_count <= 20]
    date_cols = [c.name for c in summary.columns if "date" in c.name.lower() or "time" in c.name.lower()]

    # Bar chart: first categorical vs first numeric
    if cat_cols and numeric_cols:
        specs.append(ChartSpec(
            chart_type=ChartType.bar,
            title=f"{numeric_cols[0]} by {cat_cols[0]}",
            x_column=cat_cols[0],
            y_column=numeric_cols[0],
        ))

    # Line chart: date vs numeric
    if date_cols and numeric_cols:
        specs.append(ChartSpec(
            chart_type=ChartType.line,
            title=f"{numeric_cols[0]} over time",
            x_column=date_cols[0],
            y_column=numeric_cols[0],
        ))

    # Pie chart: first categorical distribution
    if cat_cols and numeric_cols:
        specs.append(ChartSpec(
            chart_type=ChartType.pie,
            title=f"Distribution by {cat_cols[0]}",
            x_column=cat_cols[0],
            y_column=numeric_cols[0],
        ))

    # Horizontal bar: second numeric if available
    if cat_cols and len(numeric_cols) >= 2:
        specs.append(ChartSpec(
            chart_type=ChartType.hbar,
            title=f"{numeric_cols[1]} by {cat_cols[0]}",
            x_column=cat_cols[0],
            y_column=numeric_cols[1],
        ))

    # Scatter: two numeric columns
    if len(numeric_cols) >= 2:
        specs.append(ChartSpec(
            chart_type=ChartType.scatter,
            title=f"{numeric_cols[0]} vs {numeric_cols[1]}",
            x_column=numeric_cols[0],
            y_column=numeric_cols[1],
        ))

    return specs[:max_charts]
