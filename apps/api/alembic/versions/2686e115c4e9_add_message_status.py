"""add message status

Revision ID: 2686e115c4e9
Revises: 86e4529d673d
Create Date: 2026-08-09

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2686e115c4e9'
down_revision: Union[str, Sequence[str], None] = '86e4529d673d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "messages",
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="received",
        ),
    )

    op.create_index(
        "ix_messages_status",
        "messages",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_messages_status",
        table_name="messages",
    )

    op.drop_column(
        "messages",
        "status",
    )
