"""Tests for FastAPI endpoints (TDD — written before implementation)."""
from pathlib import Path

import pytest
from httpx import AsyncClient


async def test_health_check(api_client: AsyncClient):
    resp = await api_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data


async def test_upload_csv_generates_report(api_client: AsyncClient, sample_csv: Path):
    with open(sample_csv, "rb") as f:
        resp = await api_client.post(
            "/api/reports/generate",
            files={"file": ("sales.csv", f, "text/csv")},
            data={"title": "Test Sales", "report_type": "sales"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["report_id"]
    assert data["status"] in ("completed", "processing")


async def test_get_report_metadata(api_client: AsyncClient, sample_csv: Path):
    # First create a report
    with open(sample_csv, "rb") as f:
        create_resp = await api_client.post(
            "/api/reports/generate",
            files={"file": ("sales.csv", f, "text/csv")},
            data={"title": "Meta Test"},
        )
    report_id = create_resp.json()["report_id"]

    # Then fetch metadata
    resp = await api_client.get(f"/api/reports/{report_id}")
    assert resp.status_code == 200
    assert resp.json()["report_id"] == report_id


async def test_list_reports(api_client: AsyncClient, sample_csv: Path):
    # Create a report first
    with open(sample_csv, "rb") as f:
        await api_client.post(
            "/api/reports/generate",
            files={"file": ("sales.csv", f, "text/csv")},
            data={"title": "List Test"},
        )
    resp = await api_client.get("/api/reports")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1


async def test_report_types_endpoint(api_client: AsyncClient):
    resp = await api_client.get("/api/report-types")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any(t["type"] == "sales" for t in data)
