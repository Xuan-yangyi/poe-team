"""Tests for work orders domain — auth protection, validation, business logic."""
import pytest
from unittest.mock import AsyncMock, MagicMock


# ── Auth protection ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_work_orders_requires_auth(client):
    resp = await client.get("/work-orders")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_work_order_requires_auth(client):
    resp = await client.post("/work-orders", json={"idh_id": "IDH-01"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_work_order_requires_auth(client):
    resp = await client.get("/work-orders/wo-001")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_issue_work_order_requires_auth(client):
    resp = await client.post("/work-orders/wo-001/issue")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_accept_work_order_requires_auth(client):
    resp = await client.post("/work-orders/wo-001/accept")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_change_work_order_requires_auth(client):
    resp = await client.post("/work-orders/wo-001/change", json={"qty": 100})
    assert resp.status_code == 401


# ── Schema validation ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_work_order_invalid_empty(client, auth_headers):
    resp = await client.post("/work-orders", json={}, headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_work_order_invalid_no_lines(client, auth_headers):
    resp = await client.post("/work-orders", json={
        "idh_id": "IDH-01", "lines": []
    }, headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_work_order_line_negative_qty(client, auth_headers):
    resp = await client.post("/work-orders", json={
        "idh_id": "IDH-01",
        "lines": [{"material_id": "m1", "qty_ordered": -1}]
    }, headers=auth_headers)
    assert resp.status_code == 422


# ── Happy path with mocks ────────────────────────────────────────────────────

def _exec_result(all_rows=None, one_or_none=None, scalar_value=None):
    r = MagicMock()
    r.scalars.return_value.all.return_value = all_rows or []
    r.scalar_one_or_none.return_value = one_or_none
    r.scalar.return_value = scalar_value or 0
    return r


@pytest.mark.asyncio
async def test_list_work_orders_empty(client, auth_headers, mock_db):
    result = _exec_result()
    count_result = _exec_result(scalar_value=0)
    mock_db.execute = AsyncMock(side_effect=[result, count_result])

    resp = await client.get("/work-orders", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    assert data["data"] == []


@pytest.mark.asyncio
async def test_get_work_order_not_found(client, auth_headers, mock_db):
    result = _exec_result(one_or_none=None)
    mock_db.execute = AsyncMock(return_value=result)

    resp = await client.get("/work-orders/nonexistent", headers=auth_headers)
    assert resp.status_code == 404