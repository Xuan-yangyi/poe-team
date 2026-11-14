import asyncio
import os
import sys
from pathlib import Path
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Add the current directory to sys.path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Build database URL from environment (Docker-compatible), falling back to alembic.ini
_db_url = config.get_main_option("sqlalchemy.url")
_db_host = os.getenv("DB_HOST")
if _db_host:
    _db_url = (
        f"postgresql+asyncpg://{os.getenv('DB_USER', 'idh_app')}:{os.getenv('DB_PASSWORD', 'idh_dev')}"
        f"@{_db_host}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'idh_crm')}"
    )
    config.set_main_option("sqlalchemy.url", _db_url)

from app.models.base import Base
from app.auth.models import User  # noqa: F401 — registers User in Base.metadata
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
    try:
        connectable = async_engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
        await connectable.dispose()
    except Exception as e:
        # If database doesn't exist or can't connect, just continue
        # This allows alembic current and other read-only commands to work
        import sys
        print(f"Database connection warning: {type(e).__name__}: {str(e)[:80]}", file=sys.stderr)
        # For read-only commands, just configure with metadata and dialect
        context.configure(target_metadata=target_metadata, dialect_name="postgresql")
        return


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
