# Architecture — AI Report Generator

## Pipeline Flow

```
HTTP POST /api/reports/generate
           │
           ▼
    UploadFile saved to uploads_dir
           │
           ▼
    load_data(path)           ← ingest/loader.py
    .csv → csv_loader
    .xlsx → excel_loader
    .json → json_loader
           │
           ▼
    profile_dataframe(df)     ← analysis/profiler.py
    → DataSummary (per-column stats, quality score)
           │
           ▼
    compute_statistics(df)    ← analysis/statistics.py
    → correlations, outliers, trends
           │
           ▼
    detect_report_type(df)    ← analysis/detector.py
    → sales | financial | marketing | hr | generic
           │
           ▼
    recommend_charts() OR user chart_specs override
           │
           ▼
    generate_charts(df, specs) ← charts/generator.py
    → list[ChartResult] (base64 PNGs)
           │
           ▼
    generate_narrative(ai, summary, stats) ← narrative/writer.py
    → list[NarrativeSection]
    (Groq → Gemini → OpenRouter → template fallback)
           │
           ▼
    render_html(result)       ← renderer/html_renderer.py
    → .html file in reports_dir
           │
           ▼
    render_pdf(html_path)     ← renderer/pdf_renderer.py
    → .pdf file OR None (weasyprint optional)
           │
           ▼
    ReportStore.save(result)  ← storage/report_store.py
    → in-memory + JSON index
           │
           ▼
    return ReportResult JSON
```

## Module Map

| Module | Responsibility |
|--------|---------------|
| `src/app.py` | FastAPI routes, lifespan, CORS |
| `src/config.py` | Frozen Settings, lru_cache, structlog setup |
| `src/models.py` | All Pydantic models (frozen) + StrEnums |
| `src/exceptions.py` | ReportError hierarchy |
| `src/ingest/` | File loading (CSV/Excel/JSON/DB) |
| `src/analysis/` | Profiling, statistics, type detection |
| `src/charts/` | Matplotlib chart generation → base64 |
| `src/narrative/` | AI narrative + template fallback |
| `src/renderer/` | Jinja2 HTML + WeasyPrint PDF |
| `src/pipeline/` | Orchestrator — stages + timing |
| `src/services/` | AI cascade, DB, ServiceContainer |
| `src/storage/` | In-memory + JSON persistence |

## Data Models

```
ReportRequest
  ├── title: str
  ├── report_type: ReportType (auto/sales/financial/marketing/hr/generic)
  ├── options: ReportOptions
  └── chart_specs: list[ChartSpec] | None  ← user override

ReportResult
  ├── report_id, status, title, report_type, created_at
  ├── data_summary: DataSummary
  │     └── columns: list[ColumnProfile]
  ├── charts: list[ChartResult]
  │     └── spec: ChartSpec + image_base64: str
  ├── narrative_sections: list[NarrativeSection]
  ├── html_path, pdf_path
  └── stage_times_ms: dict[str, int]
```

## AI Cascade

```
call_llm(system, user)
  ├── Try Groq (llama-3.1-8b-instant)
  ├── Try Gemini (gemini-2.0-flash)
  ├── Try OpenRouter (meta-llama/llama-3.1-8b-instruct:free)
  └── All fail → return None → template fallback
```

All providers degrade gracefully if API keys are missing.
