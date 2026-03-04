from pathlib import Path

import pandas as pd

from src.config import get_settings
from src.exceptions import IngestionError
from src.ingest.csv_loader import load_csv
from src.ingest.excel_loader import load_excel
from src.ingest.json_loader import load_json

_SUPPORTED = {".csv", ".xlsx", ".xls", ".json"}


async def load_data(path: Path) -> pd.DataFrame:
    settings = get_settings()

    if path.stat().st_size == 0:
        raise IngestionError(f"File is empty: {path.name}")

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > settings.max_upload_mb:
        raise IngestionError(
            f"File too large: {size_mb:.1f}MB (max {settings.max_upload_mb}MB)"
        )

    ext = path.suffix.lower()
    if ext not in _SUPPORTED:
        raise IngestionError(f"Unsupported format: {ext!r}. Supported: {_SUPPORTED}")

    if ext == ".csv":
        return await load_csv(path)
    if ext in (".xlsx", ".xls"):
        return await load_excel(path)
    if ext == ".json":
        return await load_json(path)

    raise IngestionError(f"Unsupported format: {ext!r}")
