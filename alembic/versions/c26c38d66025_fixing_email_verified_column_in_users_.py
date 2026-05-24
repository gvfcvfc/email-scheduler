"""fixing email_verified column in users table

Revision ID: c26c38d66025
Revises: 932932837422
Create Date: 2026-05-21 03:48:52.316967

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c26c38d66025'
down_revision: Union[str, Sequence[str], None] = '932932837422'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.execute("""
        ALTER TABLE users
        ALTER COLUMN email_verified TYPE BOOLEAN
        USING CASE
            WHEN email_verified IS NULL THEN NULL
            WHEN LOWER(email_verified) IN ('true', 't', '1', 'yes', 'y') THEN TRUE
            WHEN LOWER(email_verified) IN ('false', 'f', '0', 'no', 'n') THEN FALSE
            ELSE FALSE
        END
    """)

def downgrade():
    op.execute("""
        ALTER TABLE users
        ALTER COLUMN email_verified TYPE VARCHAR
        USING CASE
            WHEN email_verified THEN 'true'
            ELSE 'false'
        END
    """)