"""Tests for inventory domain."""
import pytest
from unittest.mock import AsyncMock, MagicMock


def _exec_result(all_rows=None, one_or_none=None, scalar_value=None):
    r = MagicMock()
    r.scalars.return_value.all.return_value = all_rows or []
    r.scalar_one_or_none.return_value = one_or_none
    r.scalar.return_value = scalar_value or 0
    return r


@pytest.mark.asyncio
async def test_get_stock_requires_auth(client):
    resp = await client.get("/inventory/stock")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_stock_ledger_requires_auth(client):
    resp = await client.get("/inventory/stock-ledger?lot_id=lot-001")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_stock_ledger_missing_lot_id(client, auth_headers):
    resp = await client.get("/inventory/stock-ledger", headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_stock_empty(client, auth_headers, mock_db):
    result = _exec_result()
    count_result = _exec_result(scalar_value=0)
    mock_db.execute = AsyncMock(side_effect=[result, count_result])

    resp = await client.get("/inventory/stock", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"] == []
    assert data["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_get_stock_with_filters(client, auth_headers, mock_db):
    result = _exec_result()
    count_result = _exec_result(scalar_value=0)
    mock_db.execute = AsyncMock(side_effect=[result, count_result])

    resp = await client.get(
        "/inventory/stock?material_id=m1&status=available&page=1&page_size=10",
        headers=auth_headers)
    assert resp.status_code == 200