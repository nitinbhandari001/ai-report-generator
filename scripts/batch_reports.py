"""Batch process all files in a directory."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings
from src.ingest.loader import load_data
from src.models import ReportRequest, ReportType
from src.pipeline.processor import generate_report
from src.services import create_services


async def main(input_dir: str):
    dir_path = Path(input_dir)
    if not dir_path.exists():
        print(f"Directory not found: {input_dir}")
        return

    files = [f for f in dir_path.iterdir()
             if f.suffix.lower() in {".csv", ".xlsx", ".xls", ".json"}]
    if not files:
        print("No supported files found (.csv, .xlsx, .xls, .json)")
        return

    settings = get_settings()
    container = await create_services(settings)

    print(f"Processing {len(files)} files from {input_dir}")
    for path in files:
        print(f"\n  {path.name} ...", end=" ", flush=True)
        try:
            df = await load_data(path)
            request = ReportRequest(
                title=path.stem.replace("_", " ").title(),
                report_type=ReportType.auto,
            )
            result = await generate_report(df, request, container)
            print(f"{result.status} | {result.processing_time_ms}ms | {result.html_path}")
        except Exception as exc:
            print(f"FAILED: {exc}")

    print("\nDone.")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "sample_data"
    asyncio.run(main(target))
