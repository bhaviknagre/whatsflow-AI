from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.whatsapp_connection import (
    WhatsAppConnection,
)


def get_connections(
    db: Session,
    organization_id: UUID,
) -> list[WhatsAppConnection]:

    return list(
        db.scalars(
            select(WhatsAppConnection)
            .where(
                WhatsAppConnection.organization_id
                == organization_id,
                WhatsAppConnection.is_active.is_(True),
            )
            .order_by(
                WhatsAppConnection.created_at.desc()
            )
        )
    )