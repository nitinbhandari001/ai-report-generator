import asyncio
from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.models import ReportResult, ReportType

_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"

_TYPE_TEMPLATE: dict[str, str] = {
    "sales": "sales_report.html",
    "financial": "financial_report.html",
    "marketing": "marketing_report.html",
    "hr": "generic_report.html",
    "generic": "generic_report.html",
    "auto": "generic_report.html",
    "completed": "generic_report.html",
}


@lru_cache(maxsize=1)
def _get_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=True,
    )


def _render(result: ReportResult, report_type: ReportType, output_dir: Path) -> Path:
    env = _get_env()
    template_name = _TYPE_TEMPLATE.get(str(report_type), "generic_report.html")
    template = env.get_template(template_name)
    html_content = template.render(result=result)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{result.report_id}.html"
    out_path.write_text(html_content, encoding="utf-8")
    return out_path


async def render_html(result: ReportResult, report_type: ReportType, output_dir: Path) -> Path:
    return await asyncio.to_thread(_render, result, report_type, output_dir)
