import pytest


@pytest.mark.asyncio
async def test_login_success(client):
    resp = await client.post("/auth/login", json={
        "username": "factory_admin", "password": "admin123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    resp = await client.post("/auth/login", json={
        "username": "factory_admin", "password": "wrong"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    resp = await client.post("/auth/login", json={
        "username": "nobody", "password": "x"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client):
    # Get tokens
    resp = await client.post("/auth/login", json={
        "username": "factory_admin", "password": "admin123"
    })
    refresh = resp.json()["data"]["refresh_token"]

    # Refresh
    resp = await client.post("/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data["data"]


@pytest.mark.asyncio
async def test_refresh_invalid_token(client):
    resp = await client.post("/auth/refresh", json={"refresh_token": "bad.token.here"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client):
    resp = await client.get("/work-orders")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_with_token(client, admin_token):
    resp = await client.get("/work-orders", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    # Returns 200 because route exists (empty list), not 401
    assert resp.status_code == 200