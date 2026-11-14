"""Tests for shipments domain."""
import pytest
from unittest.mock import AsyncMock, MagicMock


def _exec_result(all_rows=None, one_or_none=None, scalar_value=None):
    r = MagicMock()
    r.scalars.return_value.all.return_value = all_rows or []
    r.scalar_one_or_none.return_value = one_or_none
    r.scalar.return_value = scalar_value or 0
    return r


@pytest.mark.asyncio
async def test_create_shipment_requires_auth(client):
    resp = await client.post("/shipments", json={"wo_id": "wo-1", "idh_id": "IDH-01"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_shipments_requires_auth(client):
    resp = await client.get("/shipments")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_shipment_requires_auth(client):
    resp = await client.get("/shipments/s-001")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_confirm_shipment_requires_auth(client):
    resp = await client.post("/shipments/s-001/confirm")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_goods_receipt_requires_auth(client):
    resp = await client.post("/goods-receipts", json={"dn_no": "DN001", "container_id": "C1"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_shipment_invalid(client, auth_headers):
    resp = await client.post("/shipments", json={}, headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_shipments_empty(client, auth_headers, mock_db):
    result = _exec_result()
    count_result = _exec_result(scalar_value=0)
    mock_db.execute = AsyncMock(side_effect=[result, count_result])

    resp = await client.get("/shipments", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"] == []


@pytest.mark.asyncio
async def test_get_shipment_not_found(client, auth_headers, mock_db):
    result = _exec_result(one_or_none=None)
    mock_db.execute = AsyncMock(return_value=result)

    resp = await client.get("/shipments/nonexistent", headers=auth_headers)
    assert resp.status_code == 404