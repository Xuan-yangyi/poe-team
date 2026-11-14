# Phase 1: Foundation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the project skeleton — FastAPI backend with PostgreSQL database schema, JWT authentication, event bus, and Vue 3 frontend scaffold. After this phase, the API server boots, all 17 tables exist, and `POST /auth/login` returns a JWT.

**Architecture:** FastAPI app under `backend/app/`, organized by business domain. Alembic for migrations. SQLAlchemy async with PostgreSQL. JWT short-lived (15min) + refresh token (24h). Sync event bus writes to `event_log` table directly (no Kafka in MVP).

**Tech Stack:** Python 3.12+, FastAPI 0.115+, SQLAlchemy 2.0 (async), Alembic, Pydantic v2, python-jose (JWT), passlib (bcrypt), fakeredis (dev), pytest + httpx (testing)

**Spec:** [ARCHITECTURE.md](../../doc/ARCHITECTURE.md), [DATABASE.md](../../doc/DATABASE.md), [API.md](../../doc/API.md)

## Global Constraints

- Python ≥ 3.12, all async handlers use `async def`
- All responses follow unified format: `{"code": 0, "message": "success", "data": {...}, "meta": {...}}`
- Error codes per API.md §1.4: 0=success, 1001=validation, 1002=not_found, 1003=conflict, 1004=unprocessable, 2001=unauthorized, 2002=forbidden_cross_tenant, 2003=forbidden_role, 3001=server_error, 3002=unavailable
- JWT access token 15min, refresh token 24h
- All timestamps ISO 8601 with timezone
- All `POST` endpoints accept `X-Idempotency-Key` header
- Pagination via `page` + `page_size` query params, response in `meta`
- Tenant isolation enforced at DB level (RLS policies applied via Alembic)
- No AI data leaves the server — private deployment only

## File Map

```
IDH_CRM/
├── backend/
│   ├── requirements.txt          # FastAPI, SQLAlchemy, Alembic, etc.
│   ├── alembic.ini               # Alembic config
│   ├── alembic/
│   │   ├── env.py                # Async Alembic env
│   │   └── versions/
│   │       └── 001_init_schema.py # All 17 tables + RLS
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI app factory
│   │   ├── config.py             # Pydantic Settings
│   │   ├── database.py           # Async engine + session
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py       # JWT encode/decode, password hash
│   │   │   ├── deps.py           # FastAPI dependencies (get_db, get_current_user)
│   │   │   ├── response.py       # Unified response model + error codes
│   │   │   └── pagination.py     # Pagination helper
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── base.py           # DeclarativeBase + TimestampMixin + TenantMixin
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── common.py         # PaginatedResponse, ErrorResponse
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── models.py         # User model
│   │   │   ├── schemas.py        # LoginRequest, TokenResponse
│   │   │   ├── router.py         # POST /auth/login, POST /auth/refresh
│   │   │   └── service.py        # authenticate, create_tokens
│   │   └── events/
│   │       ├── __init__.py
│   │       ├── models.py         # EventLog model
│   │       └── bus.py            # emit_event() sync writer
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py           # async test fixtures (DB, client)
│       └── test_auth.py          # Auth endpoint tests
├── frontend/                     # Phase 1: scaffold only
│   └── (created by npm create vue@latest)
```

---
### Task 1: Backend project skeleton

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`

**Interfaces:**
- Produces: FastAPI `app` object at `app.main:app`, `Settings` class from `app.config`

**Description:** Create the minimal FastAPI application with health check endpoint and settings loaded from environment variables.

- [ ] **Step 1: Create requirements.txt**

```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
sqlalchemy[asyncio]>=2.0.36
asyncpg>=0.30.0
alembic>=1.14.0
pydantic>=2.10.0
pydantic-settings>=2.6.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.17
fakeredis[lua]>=2.26.0
httpx>=0.28.0
pytest>=8.3.0
pytest-asyncio>=0.24.0
```

- [ ] **Step 2: Create `backend/app/__init__.py`**

```python
# IDH Collaboration Platform Backend
```

- [ ] **Step 3: Create `backend/app/config.py`**

```python
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "IDH Platform"
    debug: bool = False

    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "idh_platform"
    db_user: str = "idh_app"
    db_password: str = "idh_dev"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # JWT
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_hours: int = 24

    # Redis (fakeredis in dev)
    redis_url: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Create `backend/app/main.py`**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


app = create_app()


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Install dependencies and verify**

```bash
cd backend && pip install -r requirements.txt
```

- [ ] **Step 6: Start server and verify**

```bash
cd backend && uvicorn app.main:app --reload --port 8080
# In another terminal: curl http://localhost:8080/health
# Expected: {"status":"ok"}
```

- [ ] **Step 7: Commit**

```bash
git add backend/requirements.txt backend/app/
git commit -m "feat: FastAPI backend skeleton with health check"
```

### Task 2: Database connection and Alembic setup

**Files:**
- Create: `backend/app/database.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Modify: `backend/app/config.py` (add sync URL)

**Interfaces:**
- Produces: `async_session_factory()` from `app.database`, Alembic migration tooling

- [ ] **Step 1: Create `backend/app/database.py`**

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=20,
    max_overflow=10,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

- [ ] **Step 2: Create `backend/alembic.ini`**

```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql://idh_app:idh_dev@localhost:5432/idh_platform

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 3: Initialize Alembic and create first migration**

```bash
cd backend && alembic init alembic
# Overwrite the generated env.py with our async version below
```

- [ ] **Step 4: Create `backend/alembic/env.py`**

```python
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.models.base import Base
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 5: Create `backend/app/models/__init__.py`**

```python
from app.models.base import Base

__all__ = ["Base"]
```

- [ ] **Step 6: Verify Alembic can connect**

```bash
cd backend && alembic current
# Expected: (no output or "No current revision")
```

- [ ] **Step 7: Commit**

```bash
git add backend/alembic.ini backend/alembic/ backend/app/database.py backend/app/models/
git commit -m "feat: add async database connection and Alembic setup"
```

### Task 3: Base model and all 17 tables

**Files:**
- Create: `backend/app/models/base.py`
- Create: `backend/alembic/versions/001_init_schema.py`

**Interfaces:**
- Produces: SQLAlchemy `Base` with `TimestampMixin`, `TenantMixin`; all 17 table models in migration

- [ ] **Step 1: Create `backend/app/models/base.py`**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TenantMixin:
    tenant_id: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )


def new_uuid() -> str:
    return str(uuid.uuid4())
```

- [ ] **Step 2: Generate migration**

```bash
cd backend
# Create an empty migration first
alembic revision -m "init_schema"
```

- [ ] **Step 3: Write migration — Create `backend/alembic/versions/001_init_schema.py`**

Replace the generated empty revision with the full schema. Create these 17 tables:

```python
"""init_schema

Revision ID: 001
Revises:
Create Date: 2026-11-14
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. material
    op.create_table(
        'material',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('material_code', sa.String(50), nullable=False, unique=True),
        sa.Column('description', sa.String(500), nullable=False, default=''),
        sa.Column('unit', sa.String(20), nullable=False, default='pcs'),
        sa.Column('std_loss_rate', sa.Numeric(5, 4), nullable=False, default=0),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 2. material_alias
    op.create_table(
        'material_alias',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('material_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('material.id'), nullable=False),
        sa.Column('alias_code', sa.String(50), nullable=False),
        sa.Column('source', sa.String(50), nullable=False, default='idh'),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('material_id', 'alias_code', name='uq_material_alias'),
    )

    # 3. lot
    op.create_table(
        'lot',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('lot_no', sa.String(50), nullable=False, unique=True),
        sa.Column('material_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('material.id'), nullable=False),
        sa.Column('wafer_lot', sa.String(50), nullable=False, default=''),
        sa.Column('assembly_lot', sa.String(50), nullable=False, default=''),
        sa.Column('date_code', sa.String(10), nullable=False, default=''),
        sa.Column('status', sa.String(20), nullable=False, default='active'),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 4. work_order
    op.create_table(
        'work_order',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('wo_no', sa.String(30), nullable=False, unique=True),
        sa.Column('idh_id', sa.String(50), nullable=False, index=True),
        sa.Column('customer_id', sa.String(50), nullable=False, default=''),
        sa.Column('status', sa.String(20), nullable=False, default='draft'),
        sa.Column('due_date', sa.Date, nullable=True),
        sa.Column('confirmed_due_date', sa.Date, nullable=True),
        sa.Column('bom_ver', sa.String(20), nullable=False, default=''),
        sa.Column('settle_mode', sa.String(20), nullable=False, default='purchase'),
        sa.Column('priority', sa.SmallInteger, nullable=False, default=5),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 5. wo_line
    op.create_table(
        'wo_line',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('wo_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('work_order.id'), nullable=False),
        sa.Column('line_no', sa.SmallInteger, nullable=False),
        sa.Column('material_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('material.id'), nullable=False),
        sa.Column('qty_ordered', sa.Integer, nullable=False),
        sa.Column('qty_shipped', sa.Integer, nullable=False, default=0),
        sa.Column('qty_received', sa.Integer, nullable=False, default=0),
        sa.Column('qty_consumed', sa.Integer, nullable=False, default=0),
        sa.Column('unit_price', sa.Numeric(12, 4), nullable=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('wo_id', 'line_no', name='uq_wo_line'),
    )

    # 6. shipment
    op.create_table(
        'shipment',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('dn_no', sa.String(30), nullable=False, unique=True),
        sa.Column('wo_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('work_order.id'), nullable=False),
        sa.Column('idh_id', sa.String(50), nullable=False, index=True),
        sa.Column('status', sa.String(20), nullable=False, default='draft'),
        sa.Column('eta', sa.Date, nullable=True),
        sa.Column('carrier', sa.String(100), nullable=False, default=''),
        sa.Column('tracking_no', sa.String(100), nullable=False, default=''),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 7. shipment_line
    op.create_table(
        'shipment_line',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('shipment_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('shipment.id'), nullable=False),
        sa.Column('line_no', sa.SmallInteger, nullable=False),
        sa.Column('material_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('material.id'), nullable=False),
        sa.Column('lot_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('lot.id'), nullable=False),
        sa.Column('container_id', sa.String(50), nullable=False),
        sa.Column('parent_container_id', sa.String(50), nullable=False, default=''),
        sa.Column('container_type', sa.String(20), nullable=False, default='reel'),
        sa.Column('qty_per_container', sa.Integer, nullable=False),
        sa.Column('qty_shipped', sa.Integer, nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('shipment_id', 'line_no', name='uq_shipment_line'),
    )

    # 8. goods_receipt
    op.create_table(
        'goods_receipt',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('dn_no', sa.String(30), nullable=False),
        sa.Column('container_id', sa.String(50), nullable=False),
        sa.Column('lot_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('lot.id'), nullable=False),
        sa.Column('qty_received', sa.Integer, nullable=False),
        sa.Column('qty_shipped', sa.Integer, nullable=False),
        sa.Column('diff_reason', sa.String(20), nullable=False, default=''),
        sa.Column('received_by', sa.String(100), nullable=False, default=''),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('dn_no', 'container_id', name='uq_goods_receipt'),
    )

    # 9. stock_ledger
    op.create_table(
        'stock_ledger',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('material_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('material.id'), nullable=False),
        sa.Column('lot_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('lot.id'), nullable=False),
        sa.Column('idh_id', sa.String(50), nullable=False, default=''),
        sa.Column('owner', sa.String(20), nullable=False, default='factory'),
        sa.Column('status', sa.String(20), nullable=False, default='available'),
        sa.Column('qty_change', sa.Integer, nullable=False),
        sa.Column('qty_after', sa.Integer, nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_id', sa.String(100), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 10. issue
    op.create_table(
        'issue',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('wo_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('work_order.id'), nullable=False),
        sa.Column('lot_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('lot.id'), nullable=False),
        sa.Column('material_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('material.id'), nullable=False),
        sa.Column('qty', sa.Integer, nullable=False),
        sa.Column('operator', sa.String(100), nullable=False, default=''),
        sa.Column('scan_method', sa.String(20), nullable=False, default='h5'),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 11. wip_report
    op.create_table(
        'wip_report',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('wo_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('work_order.id'), nullable=False),
        sa.Column('process_code', sa.String(20), nullable=False),
        sa.Column('process_seq', sa.SmallInteger, nullable=False),
        sa.Column('qty_in', sa.Integer, nullable=False),
        sa.Column('qty_out', sa.Integer, nullable=False),
        sa.Column('qty_scrap', sa.Integer, nullable=False, default=0),
        sa.Column('scrap_reason', sa.String(50), nullable=False, default=''),
        sa.Column('reported_by', sa.String(100), nullable=False, default=''),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 12. fg_receipt
    op.create_table(
        'fg_receipt',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('wo_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('work_order.id'), nullable=False),
        sa.Column('sn', sa.String(100), nullable=False, unique=True),
        sa.Column('qty', sa.Integer, nullable=False, default=1),
        sa.Column('lot_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('lot.id'), nullable=False),
        sa.Column('received_by', sa.String(100), nullable=False, default=''),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 13. recon_period
    op.create_table(
        'recon_period',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('period', sa.String(7), nullable=False),
        sa.Column('idh_id', sa.String(50), nullable=False, index=True),
        sa.Column('status', sa.String(20), nullable=False, default='open'),
        sa.Column('total_items', sa.Integer, nullable=False, default=0),
        sa.Column('matched', sa.Integer, nullable=False, default=0),
        sa.Column('diff_count', sa.Integer, nullable=False, default=0),
        sa.Column('diff_rate', sa.Numeric(6, 4), nullable=False, default=0),
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('period', 'idh_id', name='uq_recon_period'),
    )

    # 14. recon_item
    op.create_table(
        'recon_item',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('period_id', sa.Integer, sa.ForeignKey('recon_period.id'), nullable=False),
        sa.Column('material_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('material.id'), nullable=False),
        sa.Column('lot_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('lot.id'), nullable=False),
        sa.Column('diff_code', sa.String(10), nullable=False),
        sa.Column('qty_a', sa.Integer, nullable=False, default=0),
        sa.Column('qty_b', sa.Integer, nullable=False, default=0),
        sa.Column('qty_c', sa.Integer, nullable=False, default=0),
        sa.Column('qty_diff', sa.Integer, nullable=False, default=0),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('dispute_reason', sa.Text, nullable=False, default=''),
        sa.Column('dispute_attachments', postgresql.JSONB, nullable=False, default=[]),
        sa.Column('dispute_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 15. adjustment
    op.create_table(
        'adjustment',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('adj_no', sa.String(30), nullable=False, unique=True),
        sa.Column('period_id', sa.Integer, sa.ForeignKey('recon_period.id'), nullable=False),
        sa.Column('recon_item_id', sa.Integer, sa.ForeignKey('recon_item.id'), nullable=False),
        sa.Column('lot_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('lot.id'), nullable=False),
        sa.Column('qty_before', sa.Integer, nullable=False),
        sa.Column('qty_after', sa.Integer, nullable=False),
        sa.Column('diff_code', sa.String(10), nullable=False),
        sa.Column('reason', sa.Text, nullable=False, default=''),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('factory_approved_by', sa.String(100), nullable=False, default=''),
        sa.Column('factory_approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('idh_approved_by', sa.String(100), nullable=False, default=''),
        sa.Column('idh_approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 16. event_log
    op.create_table(
        'event_log',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('event_type', sa.String(50), nullable=False, index=True),
        sa.Column('aggregate_type', sa.String(50), nullable=False, index=True),
        sa.Column('aggregate_id', sa.String(100), nullable=False, index=True),
        sa.Column('payload', postgresql.JSONB, nullable=False, default={}),
        sa.Column('actor_id', sa.String(100), nullable=False, default=''),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )

    # 17. conversation
    op.create_table(
        'conversation',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('conv_type', sa.String(20), nullable=False, index=True),
        sa.Column('ref_id', sa.String(100), nullable=False, index=True),
        sa.Column('title', sa.String(200), nullable=False, default=''),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 18. conversation_member
    op.create_table(
        'conversation_member',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('conversation.id'), nullable=False),
        sa.Column('user_id', sa.String(100), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('conversation_id', 'user_id', name='uq_conv_member'),
    )

    # 19. message
    op.create_table(
        'message',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('conversation.id'), nullable=False),
        sa.Column('sender_id', sa.String(100), nullable=False),
        sa.Column('msg_type', sa.String(20), nullable=False, default='text'),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('parent_msg_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 20. msg_tag
    op.create_table(
        'msg_tag',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('message_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('message.id'), nullable=False),
        sa.Column('tag_type', sa.String(30), nullable=False, index=True),
        sa.Column('tag_value', sa.String(500), nullable=False),
        sa.Column('tagged_by', sa.String(20), nullable=False, default='ai'),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 21. alert
    op.create_table(
        'alert',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('alert_type', sa.String(30), nullable=False, index=True),
        sa.Column('severity', sa.String(20), nullable=False, default='warning'),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('detail', sa.Text, nullable=False, default=''),
        sa.Column('ref_type', sa.String(30), nullable=False, default=''),
        sa.Column('ref_id', sa.String(100), nullable=False, default=''),
        sa.Column('status', sa.String(20), nullable=False, default='open', index=True),
        sa.Column('acknowledged_by', sa.String(100), nullable=False, default=''),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', sa.String(100), nullable=False, default=''),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution', sa.Text, nullable=False, default=''),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # RLS: Enable row-level security on all tenant-isolated tables
    tables_with_tenant = [
        'material', 'material_alias', 'lot', 'work_order', 'wo_line',
        'shipment', 'shipment_line', 'goods_receipt', 'stock_ledger',
        'issue', 'wip_report', 'fg_receipt', 'recon_period', 'recon_item',
        'adjustment', 'event_log', 'conversation', 'conversation_member',
        'message', 'msg_tag', 'alert',
    ]
    for table in tables_with_tenant:
        op.execute(f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY')
        op.execute(f'''
            CREATE POLICY tenant_isolation_{table} ON {table}
            USING (tenant_id = current_setting('app.tenant_id', true))
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true))
        ''')

    # Create indexes
    op.create_index('ix_event_log_aggregate', 'event_log',
                    ['aggregate_type', 'aggregate_id'])
    op.create_index('ix_event_log_created', 'event_log', ['created_at'])
    op.create_index('ix_stock_ledger_material_lot', 'stock_ledger',
                    ['material_id', 'lot_id'])
    op.create_index('ix_message_conv_created', 'message',
                    ['conversation_id', 'created_at'])


def downgrade() -> None:
    for table in [
        'msg_tag', 'message', 'conversation_member', 'conversation',
        'alert', 'adjustment', 'recon_item', 'recon_period',
        'fg_receipt', 'wip_report', 'issue', 'stock_ledger',
        'goods_receipt', 'shipment_line', 'shipment',
        'wo_line', 'work_order', 'lot', 'material_alias', 'material',
        'event_log',
    ]:
        op.drop_table(table)
```

- [ ] **Step 4: Create the database and run migration**

```bash
# Create the database (run as postgres superuser)
sudo -u postgres createdb idh_platform
sudo -u postgres psql -c "CREATE USER idh_app WITH PASSWORD 'idh_dev';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE idh_platform TO idh_app;"
sudo -u postgres psql -d idh_platform -c "GRANT ALL ON SCHEMA public TO idh_app;"

# Run migration
cd backend && alembic upgrade head
```

- [ ] **Step 5: Verify tables exist**

```bash
PGPASSWORD=idh_dev psql -h localhost -U idh_app -d idh_platform -c "\dt"
# Expected: 21 tables listed (17 business + alembic_version)
```

- [ ] **Step 6: Commit**

```bash
git add backend/alembic/versions/001_init_schema.py backend/app/models/base.py
git commit -m "feat: add all 21 tables with RLS policies and indexes"
```

### Task 4: Unified response format and error codes

**Files:**
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/response.py`
- Create: `backend/app/core/pagination.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/common.py`

**Interfaces:**
- Produces: `success_response()`, `error_response()`, `ErrorCode` enum, `paginate()` helper, `PaginatedResponse` schema

- [ ] **Step 1: Create `backend/app/core/__init__.py`**

```python
```

- [ ] **Step 2: Create `backend/app/core/response.py`**

```python
from enum import IntEnum
from typing import Any, Optional
from fastapi.responses import JSONResponse


class ErrorCode(IntEnum):
    SUCCESS = 0
    VALIDATION_ERROR = 1001
    NOT_FOUND = 1002
    CONFLICT = 1003
    UNPROCESSABLE = 1004
    UNAUTHORIZED = 2001
    FORBIDDEN_CROSS_TENANT = 2002
    FORBIDDEN_ROLE = 2003
    SERVER_ERROR = 3001
    SERVICE_UNAVAILABLE = 3002


HTTP_STATUS_MAP = {
    ErrorCode.SUCCESS: 200,
    ErrorCode.VALIDATION_ERROR: 400,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.CONFLICT: 409,
    ErrorCode.UNPROCESSABLE: 422,
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.FORBIDDEN_CROSS_TENANT: 403,
    ErrorCode.FORBIDDEN_ROLE: 403,
    ErrorCode.SERVER_ERROR: 500,
    ErrorCode.SERVICE_UNAVAILABLE: 503,
}


def success_response(
    data: Any = None,
    message: str = "success",
    meta: Optional[dict] = None,
) -> JSONResponse:
    body = {"code": ErrorCode.SUCCESS, "message": message, "data": data}
    if meta:
        body["meta"] = meta
    return JSONResponse(content=body, status_code=200)


def error_response(
    code: ErrorCode,
    message: str = "",
    detail: Any = None,
) -> JSONResponse:
    status = HTTP_STATUS_MAP.get(code, 500)
    body = {"code": code, "message": message, "data": detail}
    return JSONResponse(content=body, status_code=status)
```

- [ ] **Step 3: Create `backend/app/core/pagination.py`**

```python
from math import ceil
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


class PaginationParams:
    def __init__(self, page: int = 1, page_size: int = 20):
        self.page = max(1, page)
        self.page_size = min(max(1, page_size), 100)
        self.offset = (self.page - 1) * self.page_size


async def paginate(
    session: AsyncSession,
    stmt,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list, dict]:
    params = PaginationParams(page, page_size)
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0
    rows = (await session.execute(
        stmt.offset(params.offset).limit(params.page_size)
    )).scalars().all()
    meta = {
        "page": params.page,
        "page_size": params.page_size,
        "total": total,
        "total_pages": ceil(total / params.page_size) if total else 0,
    }
    return list(rows), meta
```

- [ ] **Step 4: Create `backend/app/schemas/__init__.py`**

```python
from app.schemas.common import PaginatedResponse

__all__ = ["PaginatedResponse"]
```

- [ ] **Step 5: Create `backend/app/schemas/common.py`**

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
```

- [ ] **Step 6: Verify by importing in Python**

```bash
cd backend && python -c "from app.core.response import ErrorCode, success_response; print(success_response({'test': 1}).body)"
# Expected: b'{"code":0,"message":"success","data":{"test":1}}'
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/core/ backend/app/schemas/
git commit -m "feat: unified response format, error codes, and pagination"
```

### Task 5: JWT authentication (login + refresh)

**Files:**
- Create: `backend/app/core/security.py`
- Create: `backend/app/core/deps.py`
- Create: `backend/app/auth/__init__.py`
- Create: `backend/app/auth/models.py`
- Create: `backend/app/auth/schemas.py`
- Create: `backend/app/auth/service.py`
- Create: `backend/app/auth/router.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_auth.py`

**Interfaces:**
- Produces: `POST /auth/login` → `{access_token, refresh_token}`, `POST /auth/refresh` → new tokens
- Consumes: `Settings.jwt_secret`, `Settings.jwt_algorithm` from `app.config`

- [ ] **Step 1: Create `backend/app/core/security.py`**

```python
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, extra_claims: Optional[dict] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    to_encode = {"sub": subject, "exp": expire, "type": "access"}
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        hours=settings.refresh_token_expire_hours
    )
    to_encode = {"sub": subject, "exp": expire, "type": "refresh"}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
```

- [ ] **Step 2: Create `backend/app/auth/models.py`**

```python
# MVP: hardcoded users table. Replace with real user model in production.
# For now, auth verifies against this in-memory store.
USERS = {
    "factory_admin": {
        "id": "user_factory_01",
        "username": "factory_admin",
        "password_hash": "",  # will be set in conftest
        "role": "factory_admin",
        "tenant_id": "factory",
    },
    "idh_op": {
        "id": "user_idh_01",
        "username": "idh_op",
        "password_hash": "",
        "role": "idh_op",
        "tenant_id": "IDH001",
        "idh_id": "IDH001",
    },
}
```

- [ ] **Step 3: Create `backend/app/auth/schemas.py`**

```python
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str
```

- [ ] **Step 4: Create `backend/app/auth/service.py`**

```python
from app.auth.models import USERS
from app.core.security import verify_password, create_access_token, create_refresh_token, hash_password
from app.core.response import ErrorCode
from app.config import get_settings


class AuthError(Exception):
    def __init__(self, code: ErrorCode, message: str):
        self.code = code
        self.message = message


def authenticate(username: str, password: str) -> dict:
    user = USERS.get(username)
    if not user:
        raise AuthError(ErrorCode.UNAUTHORIZED, "用户名或密码错误")
    if not verify_password(password, user["password_hash"]):
        raise AuthError(ErrorCode.UNAUTHORIZED, "用户名或密码错误")
    return user


def create_tokens(user: dict) -> dict:
    settings = get_settings()
    claims = {"role": user["role"], "tenant_id": user["tenant_id"]}
    if "idh_id" in user:
        claims["idh_id"] = user["idh_id"]
    access_token = create_access_token(user["id"], extra_claims=claims)
    refresh_token = create_refresh_token(user["id"])
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }
```

- [ ] **Step 5: Create `backend/app/auth/router.py`**

```python
from fastapi import APIRouter, HTTPException
from app.auth.schemas import LoginRequest, TokenResponse, RefreshRequest
from app.auth.service import authenticate, create_tokens, AuthError
from app.core.response import success_response, ErrorCode
from app.core.security import decode_token, create_access_token, create_refresh_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(body: LoginRequest):
    try:
        user = authenticate(body.username, body.password)
    except AuthError as e:
        raise HTTPException(status_code=401, detail={"code": e.code, "message": e.message})
    tokens = create_tokens(user)
    return success_response(data=tokens)


@router.post("/refresh")
async def refresh(body: RefreshRequest):
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail={
            "code": ErrorCode.UNAUTHORIZED, "message": "Invalid refresh token"
        })
    # In production, also check refresh token blacklist / rotation
    user_id = payload["sub"]
    claims = {k: v for k, v in payload.items() if k not in ("sub", "exp", "type", "iat")}
    access_token = create_access_token(user_id, extra_claims=claims)
    refresh_token = create_refresh_token(user_id)
    return success_response(data={
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 15 * 60,
    })
```

- [ ] **Step 6: Create `backend/app/core/deps.py`**

```python
from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.security import decode_token
from app.core.response import ErrorCode

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail={
            "code": ErrorCode.UNAUTHORIZED, "message": "未提供认证令牌"
        })
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail={
            "code": ErrorCode.UNAUTHORIZED, "message": "令牌无效或已过期"
        })
    return {
        "user_id": payload["sub"],
        "role": payload.get("role", ""),
        "tenant_id": payload.get("tenant_id", ""),
        "idh_id": payload.get("idh_id"),
    }


async def require_role(role: str, user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != role and user["role"] != "factory_admin":
        raise HTTPException(status_code=403, detail={
            "code": ErrorCode.FORBIDDEN_ROLE, "message": f"需要 {role} 权限"
        })
    return user
```

- [ ] **Step 7: Create `backend/tests/conftest.py`**

```python
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
```

- [ ] **Step 8: Create `backend/tests/test_auth.py`**

```python
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
```

- [ ] **Step 9: Wire auth router into main.py**

Add to `backend/app/main.py` after `app = create_app()`:

```python
from app.auth.router import router as auth_router
app.include_router(auth_router)

# Placeholder work-orders route (will be replaced in Phase 2)
@app.get("/work-orders")
async def work_orders_placeholder():
    return {"code": 0, "message": "success", "data": []}
```

- [ ] **Step 10: Run tests**

```bash
cd backend && python -m pytest tests/test_auth.py -v
# Expected: all 7 tests pass
```

- [ ] **Step 11: Commit**

```bash
git add backend/app/core/security.py backend/app/core/deps.py backend/app/auth/ backend/tests/ backend/app/main.py
git commit -m "feat: JWT authentication with login, refresh, and role-based deps"
```

### Task 6: Event bus

**Files:**
- Create: `backend/app/events/__init__.py`
- Create: `backend/app/events/models.py`
- Create: `backend/app/events/bus.py`

**Interfaces:**
- Produces: `emit_event(db, event_type, aggregate_type, aggregate_id, payload, actor_id, tenant_id)` — synchronous event writer to `event_log` table

- [ ] **Step 1: Create `backend/app/events/models.py`**

```python
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class EventLog(Base):
    __tablename__ = "event_log"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    aggregate_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    aggregate_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default={})
    actor_id: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
```

- [ ] **Step 2: Create `backend/app/events/bus.py`**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.events.models import EventLog


async def emit_event(
    db: AsyncSession,
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    payload: dict | None = None,
    actor_id: str = "",
    tenant_id: str = "",
) -> EventLog:
    event = EventLog(
        id=f"evt-{uuid.uuid4().hex[:12]}",
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload=payload or {},
        actor_id=actor_id,
        tenant_id=tenant_id,
    )
    db.add(event)
    await db.flush()
    return event
```

- [ ] **Step 3: Test event bus with a simple test**

```bash
cd backend && python -c "
import asyncio
from app.events.bus import emit_event
from app.database import async_session_factory

async def test():
    async with async_session_factory() as db:
        event = await emit_event(
            db, 'TEST.EVENT', 'test', 'test-1',
            {'key': 'value'}, 'user_1', 'factory'
        )
        print(f'Event created: {event.id}')

asyncio.run(test())
"
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/events/
git commit -m "feat: synchronous event bus writing to event_log"
```

### Task 7: Frontend scaffold

**Files:**
- Create: Vue 3 project via `npm create vue@latest`

- [ ] **Step 1: Create Vue 3 project**

```bash
cd /media/cvitek/martin.xuan/IDH_CRM
npm create vue@latest frontend -- --typescript --router --pinia --vitest --eslint
cd frontend && npm install
```

- [ ] **Step 2: Install additional dependencies**

```bash
cd frontend && npm install axios element-plus @element-plus/icons-vue
npm install -D sass @types/node
```

- [ ] **Step 3: Configure Vite proxy**

Edit `frontend/vite.config.ts` — add proxy to backend:

```typescript
server: {
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://localhost:8080',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ''),
    },
  },
},
```

- [ ] **Step 4: Verify frontend starts**

```bash
cd frontend && npm run dev
# Visit http://localhost:5173 — Vue welcome page should appear
```

- [ ] **Step 5: Commit**

```bash
git add frontend/
git commit -m "feat: Vue 3 + TypeScript + Element Plus frontend scaffold"
```

---

## Phase 1 Completion Checklist

After all tasks complete, verify:

- [ ] `uvicorn app.main:app` boots without errors
- [ ] `GET /health` returns `{"status": "ok"}`
- [ ] `POST /auth/login` with valid credentials returns JWT tokens
- [ ] `POST /auth/refresh` with valid refresh token returns new tokens
- [ ] Protected endpoints return 401 without token, 200 with valid token
- [ ] All 21 tables exist in PostgreSQL
- [ ] RLS policies enabled on all tenant tables
- [ ] `emit_event()` writes to `event_log` table
- [ ] Frontend dev server starts and proxies to backend
