"""add unique organization contact phone

Revision ID: 508048dbe5ad
Revises: 00bf6c2fe059
Create Date: 2026-08-10 16:26:27.280911

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '508048dbe5ad'
down_revision: Union[str, Sequence[str], None] = '00bf6c2fe059'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint(
        "uq_contacts_organization_phone",
        "contacts",
        ["organization_id", "phone_number"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "uq_contacts_organization_phone",
        "contacts",
        type_="unique",
    )
