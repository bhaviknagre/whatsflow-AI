import uuid

from sqlalchemy.orm import Session

from app.core.encryption import token_encryption
from app.models.whatsapp_connection import (
    WhatsAppConnection,
)
from app.repositories.whatsapp_connections import (
    create_connection,
    get_by_phone_number_id,
)


def save_connection(
    db: Session,
    *,
    organization_id: uuid.UUID,
    waba_id: str,
    phone_number_id: str,
    display_phone_number: str | None,
    verified_name: str | None,
    access_token: str,
) -> WhatsAppConnection:
    existing = get_by_phone_number_id(
        db,
        phone_number_id,
    )

    encrypted_token = (
        token_encryption.encrypt(
            access_token
        )
    )

    if existing:
        if (
            existing.organization_id
            != organization_id
        ):
            raise ValueError(
                "WhatsApp number is already "
                "connected to another organization"
            )

        existing.waba_id = waba_id
        existing.display_phone_number = (
            display_phone_number
        )
        existing.verified_name = verified_name
        existing.access_token_encrypted = (
            encrypted_token
        )
        existing.is_active = True

        db.flush()

        return existing

    return create_connection(
        db,
        organization_id=organization_id,
        waba_id=waba_id,
        phone_number_id=phone_number_id,
        display_phone_number=display_phone_number,
        verified_name=verified_name,
        access_token_encrypted=encrypted_token,
    )