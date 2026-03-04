"""FastAPI application — AI Report Generator."""
from __future__ import annotations

import shutil
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

import structlog
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from src.config import configure_logging, get_settings
from src.exceptions import ReportNotFoundError
from src.models import ReportOptions, ReportRequest, ReportResult, ReportType
from src.pipeline.processor import generate_report
from src.renderer.pdf_renderer import _check_pdf
from src.services import ServiceContainer, create_services

log = structlog.get_logger(__name__)

_container: ServiceContainer | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _container
    settings = get_settings()
    configure_logging(settings.log_level)
    _container = await create_services(settings)
    log.info("app_started", port=settings.fastapi_port)
    yield
    log.info("app_stopped")


app = FastAPI(
    title="AI Report Generator",
    description="Upload data → AI analyzes → generates professional PDF/HTML reports",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8004"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_container() -> ServiceContainer:
    if _container is None:
        raise RuntimeError("Container not initialized")
    return _container


# ── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    c = _get_container()
    disk = shutil.disk_usage(str(c.settings.reports_dir))
    return {
        "status": "ok",
        "pdf_available": _check_pdf(),
        "ai_configured": c.ai.has_providers,
        "disk_free_gb": round(disk.free / 1e9, 2),
    }


@app.post("/api/reports/generate")
async def generate_report_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form("Untitled Report"),
    report_type: str = Form("auto"),
):
    c = _get_container()
    settings = c.settings

    # Save upload
    upload_path = settings.uploads_dir / f"{uuid.uuid4()}_{file.filename}"
    upload_path.parent.mkdir(parents=True, exist_ok=True)
    with open(upload_path, "wb") as fp:
        fp.write(await file.read())

    file_size = upload_path.stat().st_size
    rtype = ReportType(report_type) if report_type in ReportType.__members__ or report_type in [e.value for e in ReportType] else ReportType.auto
    request = ReportRequest(title=title, report_type=rtype)

    # Small files: sync; large files: background
    if file_size < 1 * 1024 * 1024:
        from src.ingest.loader import load_data
        df = await load_data(upload_path)
        result = await generate_report(df, request, c)
        return result.model_dump(mode="json")
    else:
        report_id = str(uuid.uuid4())

        async def _bg():
            from src.ingest.loader import load_data
            df = await load_data(upload_path)
            await generate_report(df, request, c)

        background_tasks.add_task(_bg)
        return {"report_id": report_id, "status": "processing"}


@app.post("/api/reports/from-query")
async def generate_from_query(
    query: str,
    title: str = "Query Report",
    report_type: str = "auto",
):
    c = _get_container()
    if not c.db.is_configured:
        raise HTTPException(status_code=503, detail="DATABASE_URL not configured")
    df = await c.db.execute_query(query)
    if df.empty:
        raise HTTPException(status_code=400, detail="Query returned no rows")
    rtype = ReportType(report_type) if report_type in [e.value for e in ReportType] else ReportType.auto
    request = ReportRequest(title=title, report_type=rtype)
    result = await generate_report(df, request, c)
    return result.model_dump(mode="json")


@app.get("/api/reports/{report_id}")
async def get_report(report_id: str):
    c = _get_container()
    try:
        result = await c.store.get_report(report_id)
    except ReportNotFoundError:
        raise HTTPException(status_code=404, detail="Report not found")
    return result.model_dump(mode="json")


@app.get("/api/reports/{report_id}/html")
async def get_report_html(report_id: str):
    c = _get_container()
    try:
        result = await c.store.get_report(report_id)
    except ReportNotFoundError:
        raise HTTPException(status_code=404, detail="Report not found")
    if not result.html_path:
        raise HTTPException(status_code=404, detail="HTML not available")
    html_path = Path(result.html_path)
    # Path traversal guard
    try:
        html_path.resolve().relative_to(c.settings.reports_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Forbidden")
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="HTML file missing")
    return FileResponse(str(html_path), media_type="text/html")


@app.get("/api/reports/{report_id}/pdf")
async def get_report_pdf(report_id: str):
    if not _check_pdf():
        raise HTTPException(status_code=404, detail="PDF unavailable (weasyprint not installed)")
    c = _get_container()
    try:
        result = await c.store.get_report(report_id)
    except ReportNotFoundError:
        raise HTTPException(status_code=404, detail="Report not found")
    if not result.pdf_path:
        raise HTTPException(status_code=404, detail="PDF not available")
    pdf_path = Path(result.pdf_path)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file missing")
    return FileResponse(str(pdf_path), media_type="application/pdf")


@app.get("/api/reports")
async def list_reports():
    c = _get_container()
    reports = await c.store.list_reports()
    return [r.model_dump(mode="json") for r in reports]


@app.delete("/api/reports/{report_id}")
async def delete_report(report_id: str):
    c = _get_container()
    try:
        await c.store.delete_report(report_id)
    except ReportNotFoundError:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"deleted": report_id}


@app.post("/api/analyze")
async def analyze_only(file: UploadFile = File(...)):
    c = _get_container()
    upload_path = c.settings.uploads_dir / f"{uuid.uuid4()}_{file.filename}"
    upload_path.parent.mkdir(parents=True, exist_ok=True)
    with open(upload_path, "wb") as fp:
        fp.write(await file.read())
    from src.ingest.loader import load_data
    from src.analysis.profiler import profile_dataframe
    df = await load_data(upload_path)
    summary = await profile_dataframe(df)
    return summary.model_dump(mode="json")


@app.get("/api/report-types")
async def report_types():
    return [
        {"type": "sales", "description": "Sales performance — revenue, quantity, products"},
        {"type": "financial", "description": "Financial analysis — income, expenses, profit"},
        {"type": "marketing", "description": "Marketing analytics — campaigns, CTR, conversions"},
        {"type": "hr", "description": "HR metrics — headcount, turnover, satisfaction"},
        {"type": "generic", "description": "Generic data analysis"},
        {"type": "auto", "description": "Auto-detect report type from data"},
    ]
