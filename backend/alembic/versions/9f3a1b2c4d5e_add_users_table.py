"""add users table

Revision ID: 9f3a1b2c4d5e
Revises: 8ae839126243
Create Date: 2026-11-15 01:00:00

Replaces the MVP in-memory USERS dict with a real database table.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "9f3a1b2c4d5e"
down_revision: Union[str, None] = "8ae839126243"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.func.gen_random_uuid()),
        sa.Column("username", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(100), server_default=""),
        sa.Column("role", sa.String(30), nullable=False, index=True),
        sa.Column("tenant_id", sa.String(50), nullable=False, index=True),
        sa.Column("idh_id", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
    )

    # Insert default admin user (password: admin123)
    op.execute("""
        INSERT INTO users (username, password_hash, display_name, role, tenant_id, is_active)
        VALUES (
            'factory_admin',
            '$2b$12$KIZynmQE5V6b4vGiqdVuc.ttZv0MB73IkzmHuX9cyeyhyvSlVB6RS',
            '工厂管理员',
            'factory_admin',
            'factory',
            true
        )
        ON CONFLICT (username) DO NOTHING
    """)

    # Insert default IDH operator (password: idh123)
    op.execute("""
        INSERT INTO users (username, password_hash, display_name, role, tenant_id, idh_id, is_active)
        VALUES (
            'idh_op',
            '$2b$12$ttJ9t7HyyxavSwEZljOyTeeL0tnkYe9qjToSqwTN9xiDQitfw7hLe',
            'IDH操作员',
            'idh_op',
            'IDH001',
            'IDH001',
            true
        )
        ON CONFLICT (username) DO NOTHING
    """)


def downgrade() -> None:
    op.drop_table("users")