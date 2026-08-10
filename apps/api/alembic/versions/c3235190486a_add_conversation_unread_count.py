"""add conversation unread count

Revision ID: c3235190486a
Revises: 7fca1ce4d504
Create Date: 2026-08-09 17:02:47.561676

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3235190486a'
down_revision: Union[str, Sequence[str], None] = '7fca1ce4d504'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "conversations",
        sa.Column(
            "unread_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column(
        "conversations",
        "unread_count",
    )
