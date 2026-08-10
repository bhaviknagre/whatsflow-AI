import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.whatsapp_connection import (
    WhatsAppConnection,
)


def get_by_phone_number_id(
    db: Session,
    phone_number_id: str,
) -> WhatsAppConnection | None:
    return db.scalar(
        select(WhatsAppConnection).where(
            WhatsAppConnection.phone_number_id
            == phone_number_id,
        )
    )


def get_by_organization(
    db: Session,
    organization_id: uuid.UUID,
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


def create_connection(
    db: Session,
    *,
    organization_id: uuid.UUID,
    waba_id: str,
    phone_number_id: str,
    display_phone_number: str | None,
    verified_name: str | None,
    access_token_encrypted: str,
) -> WhatsAppConnection:
    connection = WhatsAppConnection(
        organization_id=organization_id,
        waba_id=waba_id,
        phone_number_id=phone_number_id,
        display_phone_number=display_phone_number,
        verified_name=verified_name,
        access_token_encrypted=access_token_encrypted,
        is_active=True,
    )

    db.add(connection)
    db.flush()

    return connection