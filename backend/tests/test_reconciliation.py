"""Tests for reconciliation domain."""
import pytest
from unittest.mock import AsyncMock, MagicMock


def _exec_result(all_rows=None, one_or_none=None, scalar_value=None):
    r = MagicMock()
    r.scalars.return_value.all.return_value = all_rows or []
    r.scalar_one_or_none.return_value = one_or_none
    r.scalar.return_value = scalar_value or 0
    return r


@pytest.mark.asyncio
async def test_create_period_requires_auth(client):
    resp = await client.post("/reconciliation/periods", json={
        "period": "2026-11", "idh_id": "IDH-01"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_period_requires_auth(client):
    resp = await client.get("/reconciliation/periods/1")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_items_requires_auth(client):
    resp = await client.get("/reconciliation/periods/1/items")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_dispute_item_requires_auth(client):
    resp = await client.put("/reconciliation/items/1/dispute", json={"dispute_reason": "wrong count"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_adjustment_requires_auth(client):
    resp = await client.post("/reconciliation/adjustments", json={
        "period_id": 1, "recon_item_id": 1, "lot_id": "lot-1",
        "qty_before": 100, "qty_after": 90, "diff_code": "MISMATCH"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_approve_adjustment_requires_auth(client):
    resp = await client.post("/reconciliation/adjustments/1/approve", json={
        "approved_by": "admin", "role": "factory"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_period_invalid_period_format(client, auth_headers):
    resp = await client.post("/reconciliation/periods", json={
        "period": "2026", "idh_id": "IDH-01"
    }, headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_period_not_found(client, auth_headers, mock_db):
    result = _exec_result(one_or_none=None)
    mock_db.execute = AsyncMock(return_value=result)

    resp = await client.get("/reconciliation/periods/99999", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_dispute_item_not_found(client, auth_headers, mock_db):
    result = _exec_result(one_or_none=None)
    mock_db.execute = AsyncMock(return_value=result)

    resp = await client.put("/reconciliation/items/99999/dispute",
                            json={"dispute_reason": "wrong"}, headers=auth_headers)
    assert resp.status_code == 404