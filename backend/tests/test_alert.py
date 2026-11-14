"""Tests for alerts domain."""
import pytest
from unittest.mock import AsyncMock, MagicMock


def _exec_result(all_rows=None, one_or_none=None, scalar_value=None):
    r = MagicMock()
    r.scalars.return_value.all.return_value = all_rows or []
    r.scalar_one_or_none.return_value = one_or_none
    r.scalar.return_value = scalar_value or 0
    return r


@pytest.mark.asyncio
async def test_list_alerts_requires_auth(client):
    resp = await client.get("/alerts")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_acknowledge_alert_requires_auth(client):
    resp = await client.post("/alerts/alert-1/acknowledge", json={"acknowledged_by": "admin"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_resolve_alert_requires_auth(client):
    resp = await client.post("/alerts/alert-1/resolve", json={
        "resolved_by": "admin", "resolution": "fixed"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_acknowledge_empty(client, auth_headers):
    resp = await client.post("/alerts/alert-1/acknowledge",
                             json={"acknowledged_by": ""}, headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_alerts_empty(client, auth_headers, mock_db):
    result = _exec_result()
    count_result = _exec_result(scalar_value=0)
    mock_db.execute = AsyncMock(side_effect=[result, count_result])

    resp = await client.get("/alerts", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"] == []
    assert data["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_acknowledge_not_found(client, auth_headers, mock_db):
    result = _exec_result(one_or_none=None)
    mock_db.execute = AsyncMock(return_value=result)

    resp = await client.post("/alerts/nonexistent/acknowledge",
                             json={"acknowledged_by": "admin"}, headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_resolve_not_found(client, auth_headers, mock_db):
    result = _exec_result(one_or_none=None)
    mock_db.execute = AsyncMock(return_value=result)

    resp = await client.post("/alerts/nonexistent/resolve",
                             json={"resolved_by": "admin"}, headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_alerts_with_filters(client, auth_headers, mock_db):
    result = _exec_result()
    count_result = _exec_result(scalar_value=0)
    mock_db.execute = AsyncMock(side_effect=[result, count_result])

    resp = await client.get(
        "/alerts?status=open&severity=critical&page=1&page_size=10",
        headers=auth_headers)
    assert resp.status_code == 200