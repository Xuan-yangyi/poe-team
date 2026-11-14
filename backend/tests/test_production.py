"""Tests for production domain."""
import pytest
from unittest.mock import MagicMock


@pytest.mark.asyncio
async def test_create_issue_requires_auth(client):
    resp = await client.post("/issues", json={
        "wo_id": "wo-1", "lot_id": "lot-1", "material_id": "m1", "qty": 100
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_wip_report_requires_auth(client):
    resp = await client.post("/wip-reports", json={
        "wo_id": "wo-1", "process_code": "SMT", "process_seq": 1,
        "qty_in": 100, "qty_out": 95
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_fg_receipt_requires_auth(client):
    resp = await client.post("/fg-receipts", json={
        "wo_id": "wo-1", "sn": "SN-001", "lot_id": "lot-1", "qty": 1
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_issue_invalid_qty(client, auth_headers):
    resp = await client.post("/issues", json={
        "wo_id": "wo-1", "lot_id": "lot-1", "material_id": "m1", "qty": 0
    }, headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_wip_report_scrap_exceeds_input(client, auth_headers, mock_db):
    resp = await client.post("/wip-reports", json={
        "wo_id": "wo-1", "process_code": "SMT", "process_seq": 1,
        "qty_in": 100, "qty_out": 50, "qty_scrap": 60
    }, headers=auth_headers)
    assert resp.status_code == 422
    err = resp.json()
    assert "产出+报废不能超过投入" in err["detail"]["message"]


@pytest.mark.asyncio
async def test_create_issue_success(client, auth_headers, mock_db):
    resp = await client.post("/issues", json={
        "wo_id": "wo-1", "lot_id": "lot-1", "material_id": "m1", "qty": 100
    }, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    assert data["data"]["qty"] == 100