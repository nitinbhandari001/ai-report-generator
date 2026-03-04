import asyncio
import csv
from pathlib import Path

import pandas as pd

from src.exceptions import IngestionError


def _read_csv(path: Path) -> pd.DataFrame:
    # Sniff delimiter from first 4 KB
    raw = path.read_bytes()
    sample = raw[:4096].decode("utf-8", errors="replace")
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ","

    # Try UTF-8, fallback to latin-1
    for enc in ("utf-8", "latin-1"):
        try:
            return pd.read_csv(path, sep=delimiter, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise IngestionError(f"Cannot decode {path} with utf-8 or latin-1")


async def load_csv(path: Path) -> pd.DataFrame:
    return await asyncio.to_thread(_read_csv, path)
