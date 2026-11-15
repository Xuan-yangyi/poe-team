"""add_agents_and_skills

Revision ID: bebd62eb033f
Revises: 9f3a1b2c4d5e
Create Date: 2026-11-15 08:02:30.604578

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bebd62eb033f'
down_revision: Union[str, Sequence[str], None] = '9f3a1b2c4d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('agents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('avatar_emoji', sa.String(length=10), nullable=False),
        sa.Column('role_description', sa.Text(), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('model', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agents_tenant_id'), 'agents', ['tenant_id'], unique=False)

    op.create_table('agent_skills',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('agent_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('trigger_keywords', sa.Text(), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('skill_prompt', sa.Text(), nullable=False),
        sa.Column('data_config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_skills_tenant_id'), 'agent_skills', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_agent_skills_tenant_id'), table_name='agent_skills')
    op.drop_table('agent_skills')
    op.drop_index(op.f('ix_agents_tenant_id'), table_name='agents')
    op.drop_table('agents')