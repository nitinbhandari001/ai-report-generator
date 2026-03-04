import asyncio
import json
from pathlib import Path

import pandas as pd

from src.exceptions import IngestionError


def _read_json(path: Path) -> pd.DataFrame:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return pd.DataFrame(data)
    if isinstance(data, dict):
        return pd.json_normalize(data)
    raise IngestionError(f"JSON root must be array or object, got {type(data)}")


async def load_json(path: Path) -> pd.DataFrame:
    return await asyncio.to_thread(_read_json, path)
