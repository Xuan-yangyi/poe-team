"""Integration test fixtures — real PostgreSQL database."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.main import app
from app.core.security import hash_password
from app.database import get_db

DATABASE_URL = "postgresql+asyncpg://idh_app:idh_dev@localhost:5433/idh_crm"
TENANT_ID = "factory"

# Pre-compute password hashes (same for every test run)
_ADMIN_HASH = hash_password("admin123")
_IDH_HASH = hash_password("idh123")


@pytest_asyncio.fixture(autouse=True)
async def seed_test_users(db_session):
    """Seed default users into the database before each test."""
    await db_session.execute(text("""
        INSERT INTO users (id, username, password_hash, display_name, role, tenant_id, idh_id, is_active)
        VALUES
            ('a0000000-0000-0000-0000-000000000001', 'factory_admin', :admin_hash,
             'Factory Admin', 'factory_admin', 'factory', NULL, true),
            ('b0000000-0000-0000-0000-000000000001', 'idh_op', :idh_hash,
             'IDH Operator', 'idh_op', 'IDH001', 'IDH001', true)
        ON CONFLICT (username) DO UPDATE SET password_hash = EXCLUDED.password_hash
    """), {"admin_hash": _ADMIN_HASH, "idh_hash": _IDH_HASH})
    await db_session.flush()


@pytest_asyncio.fixture
async def db_session():
    """Real async database session with tenant context."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(text(f"SET app.tenant_id = '{TENANT_ID}'"))
        yield session
        await session.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    """HTTP client with real DB dependency override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_token(client):
    resp = await client.post("/auth/login", json={
        "username": "factory_admin", "password": "admin123"
    })
    return resp.json()["data"]["access_token"]


@pytest_asyncio.fixture
async def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest_asyncio.fixture
async def test_materials(db_session):
    """Seed test materials for FK satisfaction."""
    mat_ids = [
        "00000000-0000-0000-0000-000000000001",
        "00000000-0000-0000-0000-000000000002",
        "00000000-0000-0000-0000-000000000003",
    ]
    for i, mid in enumerate(mat_ids, 1):
        await db_session.execute(
            text("""
                INSERT INTO material (id, material_code, description, unit, std_loss_rate, is_active, tenant_id)
                VALUES (:id, :code, '', 'pcs', 0, true, :tid)
                ON CONFLICT (id) DO NOTHING
            """),
            {"id": mid, "code": f"MAT-TEST-{i:03d}", "tid": TENANT_ID}
        )
    await db_session.flush()


@pytest_asyncio.fixture
async def test_lots(db_session):
    """Seed test lots for FK satisfaction."""
    lot_ids = [
        "00000000-0000-0000-0000-000000000001",
        "00000000-0000-0000-0000-000000000002",
        "00000000-0000-0000-0000-000000000003",
    ]
    for i, lid in enumerate(lot_ids, 1):
        await db_session.execute(
            text("""
                INSERT INTO lot (id, lot_no, material_id, wafer_lot, assembly_lot, date_code, status, tenant_id)
                VALUES (:id, :lot_no, :mid, '', '', '', 'active', :tid)
                ON CONFLICT (id) DO NOTHING
            """),
            {"id": lid, "lot_no": f"LOT-TEST-{i:03d}", "mid": lid, "tid": TENANT_ID}
        )
    await db_session.flush()