"""use timezone aware timestamps

Revision ID: 5363ecee3e70
Revises: b7bf0dddacb1
Create Date: 2026-10-18 11:02:30.016993

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5363ecee3e70'
down_revision: Union[str, Sequence[str], None] = 'b7bf0dddacb1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# every DateTime column that moves from TIMESTAMP to TIMESTAMPTZ
TIMESTAMP_COLUMNS = [
    ("devices", "created_at"),
    ("devices", "updated_at"),
    ("readings", "timestamp"),
    ("readings", "created_at"),
]


def upgrade() -> None:
    """Upgrade schema."""
    # existing naive values were written in UTC, so read them as UTC while converting
    for table, column in TIMESTAMP_COLUMNS:
        op.alter_column(
            table,
            column,
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
            postgresql_using=f"\"{column}\" AT TIME ZONE 'UTC'",
        )


def downgrade() -> None:
    """Downgrade schema."""
    for table, column in TIMESTAMP_COLUMNS:
        op.alter_column(
            table,
            column,
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=False,
            postgresql_using=f"\"{column}\" AT TIME ZONE 'UTC'",
        )
