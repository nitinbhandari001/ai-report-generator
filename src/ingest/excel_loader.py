import asyncio
from pathlib import Path

import pandas as pd


def _read_excel(path: Path, sheet: str | None) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name=sheet or 0, engine="openpyxl")


async def load_excel(path: Path, sheet: str | None = None) -> pd.DataFrame:
    return await asyncio.to_thread(_read_excel, path, sheet)
