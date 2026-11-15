"""add_llm_configs

Revision ID: c1d2e3f4a5b6
Revises: bebd62eb033f
Create Date: 2026-11-15 08:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, Sequence[str], None] = 'bebd62eb033f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('llm_configs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('api_base', sa.String(length=500), nullable=False),
        sa.Column('api_key', sa.Text(), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('extra_params', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_llm_configs_tenant_id'), 'llm_configs', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_llm_configs_tenant_id'), table_name='llm_configs')
    op.drop_table('llm_configs')