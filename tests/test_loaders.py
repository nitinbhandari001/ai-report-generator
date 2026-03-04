"""Tests for data loaders (TDD — written before implementation)."""
import json
from pathlib import Path

import pandas as pd
import pytest

from src.exceptions import IngestionError
from src.ingest.loader import load_data


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def csv_file(tmp_path: Path) -> Path:
    p = tmp_path / "sales.csv"
    p.write_text("product,revenue,quantity\nWidget,100,5\nGadget,200,3\n", encoding="utf-8")
    return p


@pytest.fixture
def csv_latin1_file(tmp_path: Path) -> Path:
    p = tmp_path / "sales_latin1.csv"
    content = "product,revenue\nCafé,100\nNaïve,200\n"
    p.write_bytes(content.encode("latin-1"))
    return p


@pytest.fixture
def excel_file(tmp_path: Path) -> Path:
    p = tmp_path / "data.xlsx"
    df = pd.DataFrame({"col_a": [1, 2], "col_b": ["x", "y"]})
    df.to_excel(p, index=False)
    return p


@pytest.fixture
def json_file(tmp_path: Path) -> Path:
    p = tmp_path / "data.json"
    records = [{"name": "Alice", "score": 90}, {"name": "Bob", "score": 85}]
    p.write_text(json.dumps(records), encoding="utf-8")
    return p


@pytest.fixture
def empty_csv(tmp_path: Path) -> Path:
    p = tmp_path / "empty.csv"
    p.write_bytes(b"")
    return p


# ── Tests ─────────────────────────────────────────────────────────────────────

async def test_load_csv_basic(csv_file: Path):
    df = await load_data(csv_file)
    assert list(df.columns) == ["product", "revenue", "quantity"]
    assert len(df) == 2
    assert df["revenue"].iloc[0] == 100


async def test_load_csv_encoding(csv_latin1_file: Path):
    df = await load_data(csv_latin1_file)
    assert len(df) == 2
    assert "product" in df.columns


async def test_load_excel(excel_file: Path):
    df = await load_data(excel_file)
    assert list(df.columns) == ["col_a", "col_b"]
    assert len(df) == 2


async def test_load_json_records(json_file: Path):
    df = await load_data(json_file)
    assert "name" in df.columns
    assert "score" in df.columns
    assert len(df) == 2


async def test_unsupported_format_raises(tmp_path: Path):
    p = tmp_path / "data.parquet"
    p.write_bytes(b"fake")
    with pytest.raises(IngestionError, match="Unsupported"):
        await load_data(p)


async def test_empty_file_raises(empty_csv: Path):
    with pytest.raises(IngestionError, match="empty"):
        await load_data(empty_csv)
