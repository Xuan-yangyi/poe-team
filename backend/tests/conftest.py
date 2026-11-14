import uuid
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from app.main import app
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


def make_mock_user(*, username="factory_admin", password="admin123",
                   role="factory_admin", tenant_id="factory",
                   idh_id=None, is_active=True):
    """Create a mock User-like object for unit tests."""
    user = MagicMock()
    user.id = uuid.UUID("a0000000-0000-0000-0000-000000000001")
    user.username = username
    user.password_hash = hash_password(password)
    user.display_name = "Test User"
    user.role = role
    user.tenant_id = tenant_id
    user.idh_id = idh_id
    user.is_active = is_active
    user.last_login_at = None
    return user


_factory_admin = make_mock_user()
_idh_op = make_mock_user(username="idh_op", password="idh123",
                          role="idh_op", tenant_id="IDH001", idh_id="IDH001")


@pytest.fixture(autouse=True)
def mock_db():
    """Override get_db with a mock AsyncSession that knows about test users."""
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.flush = AsyncMock()
    # add/merge are sync ORM methods — must NOT be AsyncMock
    mock_session.add = MagicMock()
    mock_session.merge = MagicMock()

    # Return the correct user based on the query
    async def mock_execute(statement, *args, **kwargs):
        result = MagicMock()
        result.scalars = MagicMock()
        result.scalar = MagicMock(return_value=0)

        # Compile the statement to check username
        try:
            compiled = str(statement.compile(compile_kwargs={"literal_binds": True}))
        except Exception:
            compiled = str(statement)

        if "'factory_admin'" in compiled:
            result.scalars.return_value.all.return_value = [_factory_admin]
            result.scalar_one_or_none = MagicMock(return_value=_factory_admin)
        elif "'idh_op'" in compiled:
            result.scalars.return_value.all.return_value = [_idh_op]
            result.scalar_one_or_none = MagicMock(return_value=_idh_op)
        else:
            result.scalars.return_value.all.return_value = []
            result.scalar_one_or_none = MagicMock(return_value=None)
        return result

    mock_session.execute = mock_execute

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