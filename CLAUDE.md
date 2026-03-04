# CLAUDE.md — AI Report Generator

## Commands

```bash
# Run server
uvicorn src.app:app --port 8004 --reload

# Tests
pytest tests/ -v              # all 31
pytest tests/test_api.py -v   # API only

# Sample data
py scripts/generate_sample_data.py
py scripts/demo.py

# Verify config
py -c "from src.config import get_settings; print(get_settings().fastapi_port)"
```

## Architecture

```
Upload → load_data() → profile_dataframe() → compute_statistics()
      → detect_report_type() → recommend_charts() / user override
      → generate_charts() → generate_narrative()
      → render_html() → render_pdf() → ReportStore.save()
```

## Key Patterns

- **Frozen Settings dataclass** + `from_env()` + `lru_cache` (`src/config.py`)
- **LLMProvider + AIService cascade**: Groq → Gemini → OpenRouter (`src/services/ai.py`)
- **ServiceContainer** dataclass + `create_services()` (`src/services/__init__.py`)
- **asynccontextmanager lifespan** + module-level `_container` (`src/app.py`)
- `ConfigDict(frozen=True)` on all Pydantic models, `StrEnum`
- All pandas/matplotlib work via `asyncio.to_thread`

## Gotchas

- pandas 3.x: use `.ffill()` not `.fillna(method='ffill')`
- matplotlib: always `matplotlib.use("Agg")` — no GUI on server
- WeasyPrint: catch `Exception` (not just `ImportError`) — `OSError` on Windows (GTK3 missing)
- All paths: `Path(__file__).parent.parent / ...` — never CWD-relative
- STDIO mode: no interactive input needed
- Jinja2 env: `@lru_cache` on `_get_env()` — one instance per process

## File Layout

```
src/
  app.py              FastAPI app, 10 endpoints
  config.py           Settings, configure_logging
  exceptions.py       ReportError hierarchy
  models.py           All Pydantic models + enums
  ingest/             csv/excel/json/db loaders + dispatcher
  analysis/           profiler, statistics, detector
  charts/             palette, encoders, generator
  narrative/          templates, writer
  renderer/           html_renderer, pdf_renderer
  pipeline/           processor (orchestrator)
  services/           ai, database, ServiceContainer
  storage/            report_store
templates/            Jinja2 HTML templates
```
