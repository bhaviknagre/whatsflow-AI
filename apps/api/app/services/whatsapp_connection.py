from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.encryption import token_encryption
from app.models.whatsapp_connection import WhatsAppConnection


def save_connection(
    db: Session,
    *,
    organization_id: UUID,
    waba_id: str,
    phone_number_id: str,
    display_phone_number: str | None,
    verified_name: str | None,
    access_token: str,
    expires_at: datetime | None = None,
) -> WhatsAppConnection:
    connection = db.scalar(
        select(WhatsAppConnection).where(
            WhatsAppConnection.organization_id == organization_id,
            WhatsAppConnection.phone_number_id == phone_number_id,
        )
    )

    access_token_encrypted = token_encryption.encrypt(access_token)

    if connection is None:
        connection = WhatsAppConnection(
            organization_id=organization_id,
            waba_id=waba_id,
            phone_number_id=phone_number_id,
            display_phone_number=display_phone_number,
            verified_name=verified_name,
            access_token_encrypted=access_token_encrypted,
            expires_at=expires_at,
        )
        db.add(connection)
    else:
        connection.waba_id = waba_id
        connection.display_phone_number = display_phone_number
        connection.verified_name = verified_name
        connection.access_token_encrypted = access_token_encrypted
        connection.expires_at = expires_at
        connection.is_active = True

    db.flush()
    db.refresh(connection)

    return connection
