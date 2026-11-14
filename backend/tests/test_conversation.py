"""Tests for conversations domain."""
import pytest
from unittest.mock import AsyncMock, MagicMock


def _exec_result(all_rows=None, one_or_none=None, scalar_value=None):
    r = MagicMock()
    r.scalars.return_value.all.return_value = all_rows or []
    r.scalar_one_or_none.return_value = one_or_none
    r.scalar.return_value = scalar_value or 0
    return r


@pytest.mark.asyncio
async def test_create_conversation_requires_auth(client):
    resp = await client.post("/conversations", json={
        "conv_type": "wo", "ref_id": "wo-001"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_conversations_requires_auth(client):
    resp = await client.get("/conversations")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_post_message_requires_auth(client):
    resp = await client.post("/conversations/conv-1/messages", json={"content": "hello"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_messages_requires_auth(client):
    resp = await client.get("/conversations/conv-1/messages")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_add_tag_requires_auth(client):
    resp = await client.post("/conversations/tags", json={
        "message_id": "msg-1", "tag_type": "urgency", "tag_value": "high"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_post_message_empty_content(client, auth_headers):
    resp = await client.post("/conversations/conv-1/messages",
                             json={"content": ""}, headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_conversations_empty(client, auth_headers, mock_db):
    result = _exec_result()
    mock_db.execute = AsyncMock(return_value=result)

    resp = await client.get("/conversations", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"] == []


@pytest.mark.asyncio
async def test_get_conversation_not_found(client, auth_headers, mock_db):
    result = _exec_result(one_or_none=None)
    mock_db.execute = AsyncMock(return_value=result)

    resp = await client.get("/conversations/nonexistent", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_tag_validation_invalid_confidence(client, auth_headers):
    resp = await client.post("/conversations/tags", json={
        "message_id": "msg-1", "tag_type": "sentiment",
        "tag_value": "positive", "confidence": 1.5
    }, headers=auth_headers)
    assert resp.status_code == 422