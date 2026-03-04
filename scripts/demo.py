"""Demo: upload each sample file and generate a report."""
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings
from src.ingest.loader import load_data
from src.models import ReportRequest, ReportType
from src.pipeline.processor import generate_report
from src.services import create_services

SAMPLE_DIR = Path(__file__).parent.parent / "sample_data"

SAMPLES = [
    ("sales_data.csv", "Sales Performance 2023", ReportType.sales),
    ("financial_data.xlsx", "Financial Overview 2023", ReportType.financial),
    ("marketing_data.json", "Marketing Analytics 2023", ReportType.marketing),
    ("hr_metrics.csv", "HR Metrics 2022-2024", ReportType.hr),
]


async def main():
    settings = get_settings()
    container = await create_services(settings)

    for filename, title, rtype in SAMPLES:
        path = SAMPLE_DIR / filename
        if not path.exists():
            print(f"  SKIP {filename} (not found — run scripts/generate_sample_data.py first)")
            continue
        print(f"\nProcessing: {filename}")
        df = await load_data(path)
        request = ReportRequest(title=title, report_type=rtype)
        result = await generate_report(df, request, container)
        print(f"  Status: {result.status}")
        print(f"  Rows: {result.data_summary.row_count if result.data_summary else 'N/A'}")
        print(f"  Charts: {len(result.charts)}")
        print(f"  Sections: {len(result.narrative_sections)}")
        print(f"  HTML: {result.html_path}")
        print(f"  Time: {result.processing_time_ms}ms")


if __name__ == "__main__":
    asyncio.run(main())
