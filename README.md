# AI Report Generator

Upload data → AI analyzes → generates professional PDF/HTML reports with charts, tables, and narrative insights.

## Features

- Ingest CSV, Excel (.xlsx/.xls), JSON, or PostgreSQL query results
- AI narrative (Groq → Gemini → OpenRouter cascade, degrades gracefully without keys)
- Auto-detects report type (sales, financial, marketing, HR, generic)
- Generates up to 6 charts (bar, line, pie, horizontal bar, scatter)
- Exports to HTML (always) and PDF (optional, requires WeasyPrint)
- REST API with 10 endpoints

## Quick Start

### Windows

```bash
cd C:\Users\Nitin\portfolio\ai-report-generator
py -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
# Optional PDF support (requires GTK3 runtime: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer)
# pip install -e ".[dev,pdf]"
cp .env.template .env   # fill in API keys
uvicorn src.app:app --port 8004 --reload
```

### macOS

```bash
cd ~/portfolio/ai-report-generator
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
# Optional PDF support:
# brew install weasyprint && pip install -e ".[dev,pdf]"
cp .env.template .env
uvicorn src.app:app --port 8004 --reload
```

## Generate Sample Data

```bash
python scripts/generate_sample_data.py
python scripts/demo.py        # process all sample files
python scripts/batch_reports.py sample_data/  # batch any directory
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/reports/generate` | Upload file → generate report |
| `POST` | `/api/reports/from-query` | SQL query → generate report (needs DATABASE_URL) |
| `GET` | `/api/reports/{id}` | Get report metadata |
| `GET` | `/api/reports/{id}/html` | Download HTML report |
| `GET` | `/api/reports/{id}/pdf` | Download PDF (404 if weasyprint unavailable) |
| `GET` | `/api/reports` | List all reports |
| `DELETE` | `/api/reports/{id}` | Delete report + files |
| `POST` | `/api/analyze` | Profile data only (no full report) |
| `GET` | `/api/report-types` | List available report types |
| `GET` | `/health` | Health check + capability status |

### Upload Example (curl)

```bash
curl -X POST http://localhost:8004/api/reports/generate \
  -F "file=@sample_data/sales_data.csv" \
  -F "title=Sales Q1 2024" \
  -F "report_type=sales"
```

## Sample Data

| File | Rows | Description |
|------|------|-------------|
| `sales_data.csv` | 500 | Product sales with seasonal trends |
| `financial_data.xlsx` | 200 | Income/expense with quarterly spikes |
| `marketing_data.json` | 300 | Campaign performance across 5 channels |
| `hr_metrics.csv` | 192 | Workforce metrics with training-satisfaction correlation |

## Environment Variables

```
GROQ_API_KEY=          # Optional — enables AI narrative
GEMINI_API_KEY=        # Optional — fallback AI
OPENROUTER_API_KEY=    # Optional — second fallback
DATABASE_URL=          # Optional — enables /api/reports/from-query
FASTAPI_PORT=8004
MAX_UPLOAD_MB=50
```

## WeasyPrint Notes

- **Windows**: GTK3 runtime required for PDF. Without it, `render_pdf` catches `OSError` and returns `None` gracefully. HTML reports always work.
- **macOS**: `brew install weasyprint` before `pip install -e ".[dev,pdf]"`

## Run Tests

```bash
pytest tests/ -v   # 31 tests
```
