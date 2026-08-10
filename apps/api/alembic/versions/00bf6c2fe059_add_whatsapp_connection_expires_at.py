"""add whatsapp connection expires_at

Revision ID: 00bf6c2fe059
Revises: b20f0eca4b99
Create Date: 2026-08-10 15:30:50.959521

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '00bf6c2fe059'
down_revision: Union[str, Sequence[str], None] = 'b20f0eca4b99'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'whatsapp_connections',
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('whatsapp_connections', 'expires_at')
