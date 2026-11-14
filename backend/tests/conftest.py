import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.auth.models import USERS
from app.core.security import hash_password


@pytest.fixture(autouse=True)
def setup_users():
    USERS["factory_admin"]["password_hash"] = hash_password("admin123")
    USERS["idh_op"]["password_hash"] = hash_password("idh123")


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_token(client):
    resp = await client.post("/auth/login", json={
        "username": "factory_admin", "password": "admin123"
    })
    data = resp.json()
    return data["data"]["access_token"]


@pytest_asyncio.fixture
async def idh_token(client):
    resp = await client.post("/auth/login", json={
        "username": "idh_op", "password": "idh123"
    })
    data = resp.json()
    return data["data"]["access_token"]