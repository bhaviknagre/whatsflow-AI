from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message

ALLOWED_STATUSES = {
    "pending",
    "sent",
    "delivered",
    "read",
    "failed",
    "received",
}

STATUS_ORDER = {
    "pending": 0,
    "sent": 1,
    "delivered": 2,
    "read": 3,
}


def update_message_status(
    db: Session,
    *,
    whatsapp_message_id: str,
    status: str,
) -> tuple[Message | None, bool]:
    if status not in ALLOWED_STATUSES:
        return None, False

    message = db.scalar(
        select(Message).where(
            Message.whatsapp_message_id
            == whatsapp_message_id
        )
    )

    if message is None:
        return None, False

    previous_status = message.status

    current_rank = STATUS_ORDER.get(
        message.status,
        0,
    )

    new_rank = STATUS_ORDER.get(
        status,
        current_rank,
    )

    if status in {
        "failed",
        "received",
    } or new_rank >= current_rank:
        message.status = status

    return message, message.status != previous_status


def get_message_organization_id(
    db: Session,
    message: Message,
) -> UUID | None:
    return db.scalar(
        select(
            Conversation.organization_id
        ).where(
            Conversation.id
            == message.conversation_id
        )
    )
