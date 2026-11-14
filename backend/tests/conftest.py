import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.auth.models import USERS
from app.core.security import hash_password
from app.database import get_db


def _make_exec_result(*, all_rows=None, one_or_none=None, scalar_value=None):
    """Build a mock result object for db.execute() returns."""
    mock_result = MagicMock()
    mock_result.scalars = MagicMock()
    mock_result.scalars.return_value.all = MagicMock(return_value=all_rows or [])
    mock_result.scalar_one_or_none = MagicMock(return_value=one_or_none)
    mock_result.scalar = MagicMock(return_value=scalar_value or 0)
    return mock_result


@pytest.fixture(autouse=True)
def setup_users():
    USERS["factory_admin"]["password_hash"] = hash_password("admin123")
    USERS["idh_op"]["password_hash"] = hash_password("idh123")


@pytest.fixture(autouse=True)
def mock_db():
    """Override get_db with a mock AsyncSession. Default execute returns empty."""
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.flush = AsyncMock()
    # Default: empty results, no scalars found
    mock_session.execute = AsyncMock(return_value=_make_exec_result())

    async def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db
    yield mock_session
    app.dependency_overrides.clear()


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


@pytest_asyncio.fixture
async def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}