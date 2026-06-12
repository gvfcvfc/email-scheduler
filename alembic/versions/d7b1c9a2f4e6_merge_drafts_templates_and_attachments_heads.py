"""merge drafts templates and attachments heads

Revision ID: d7b1c9a2f4e6
Revises: a4d1272f1e04, 97c30b4f6a1d
Create Date: 2026-06-07 00:00:00.000000

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = 'd7b1c9a2f4e6'
down_revision: Union[str, Sequence[str], None] = ('a4d1272f1e04', '97c30b4f6a1d')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
