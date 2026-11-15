"""add_avatar_emoji_and_conversation_preview

Revision ID: 85a9f001e922
Revises: c1d2e3f4a5b6
Create Date: 2026-11-15 12:48:31.220115

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '85a9f001e922'
down_revision: Union[str, Sequence[str], None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('avatar_emoji', sa.String(10), server_default='', nullable=False))
    op.add_column('users', sa.Column('avatar_url', sa.String(500), server_default='', nullable=False))
    op.add_column('users', sa.Column('email', sa.String(200), server_default='', nullable=False))
    op.add_column('conversation', sa.Column('last_msg_preview', sa.String(200), nullable=True))
    op.add_column('conversation', sa.Column('last_msg_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('conversation', 'last_msg_at')
    op.drop_column('conversation', 'last_msg_preview')
    op.drop_column('users', 'email')
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'avatar_emoji')