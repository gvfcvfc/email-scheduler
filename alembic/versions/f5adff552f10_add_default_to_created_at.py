"""add default to created_at

Revision ID: f5adff552f10
Revises: febee8b6a717
Create Date: 2026-03-18 20:29:06.422986

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f5adff552f10'
down_revision: Union[str, Sequence[str], None] = 'febee8b6a717'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
    "refresh_tokens",
    "created_at",
    server_default=sa.func.now()
)


def downgrade() -> None:
    """Downgrade schema."""
    pass
