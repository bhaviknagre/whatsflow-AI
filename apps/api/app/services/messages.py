import re
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.encryption import token_encryption
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.whatsapp_connection import (
    WhatsAppConnection,
)
from app.schemas.meta_webhook import (
    IncomingWhatsAppMessage,
)
from app.services.contacts import get_or_create_contact
from app.services.meta_whatsapp import (
    MetaWhatsAppClient,
)

_NON_DIGIT_PATTERN = re.compile(r"\D")


def normalize_phone_number(value: str) -> str:
    return _NON_DIGIT_PATTERN.sub("", value)


def render_template_body(
    body_text: str | None,
    parameters: list[str],
) -> str:
    rendered_text = body_text or ""

    for index, value in enumerate(
        parameters,
        start=1,
    ):
        rendered_text = rendered_text.replace(
            f"{{{{{index}}}}}",
            value,
        )

    return rendered_text


def get_or_create_conversation(
    db: Session,
    *,
    organization_id: UUID,
    whatsapp_connection: WhatsAppConnection,
    customer_phone_number: str,
) -> Conversation:
    conversation = db.scalar(
        select(Conversation)
        .where(
            Conversation.organization_id
            == organization_id,
            Conversation.whatsapp_connection_id
            == whatsapp_connection.id,
            Conversation.customer_phone_number
            == customer_phone_number,
            Conversation.deleted_at.is_(None),
        )
    )

    if conversation:
        return conversation

    conversation = Conversation(
        organization_id=organization_id,
        whatsapp_connection_id=(
            whatsapp_connection.id
        ),
        customer_phone_number=(
            customer_phone_number
        ),
    )

    db.add(conversation)
    db.flush()

    return conversation


def persist_incoming_message(
    db: Session,
    *,
    organization_id: UUID,
    whatsapp_connection: WhatsAppConnection,
    message: IncomingWhatsAppMessage,
) -> tuple[Message, bool]:
    existing = db.scalar(
        select(Message)
        .where(
            Message.whatsapp_message_id
            == message.message_id
        )
    )

    if existing:
        return existing, False

    customer_phone_number = normalize_phone_number(
        message.from_phone_number
    )

    get_or_create_contact(
        db,
        organization_id=organization_id,
        phone_number=customer_phone_number,
        profile_name=message.profile_name,
    )

    conversation = get_or_create_conversation(
        db,
        organization_id=organization_id,
        whatsapp_connection=(
            whatsapp_connection
        ),
        customer_phone_number=customer_phone_number,
    )

    conversation.unread_count += 1

    db_message = Message(
    conversation_id=conversation.id,
    whatsapp_message_id=message.message_id,
    sender_phone_number=customer_phone_number,
    direction="inbound",
    status="received",
    message_type=message.message_type,
    text=message.text,
    whatsapp_timestamp=message.timestamp,
    )

    db.add(db_message)
    db.flush()

    return db_message, True

async def send_outbound_message(
    db: Session,
    *,
    organization_id: UUID,
    conversation: Conversation,
    text: str,
) -> Message:
    if conversation.organization_id != organization_id:
        raise ValueError(
            "Conversation does not belong to organization"
        )

    whatsapp_connection = (
        conversation.whatsapp_connection
    )

    if (
        whatsapp_connection is None
        or not whatsapp_connection.is_active
    ):
        raise ValueError(
            "WhatsApp connection is not active"
        )

    client = MetaWhatsAppClient()

    access_token = token_encryption.decrypt(
        whatsapp_connection.access_token_encrypted
    )

    result = await client.send_text_message(
        phone_number_id=(
            whatsapp_connection.phone_number_id
        ),
        access_token=access_token,
        recipient_phone_number=(
            conversation.customer_phone_number
        ),
        text=text,
    )

    message = Message(
        conversation_id=conversation.id,
        whatsapp_message_id=result.message_id,
        sender_phone_number=(
            whatsapp_connection.display_phone_number
            or whatsapp_connection.phone_number_id
        ),
        direction="outbound",
        status="sent",
        message_type="text",
        text=text,
        whatsapp_timestamp=str(
            int(datetime.now(UTC).timestamp())
        ),
    )

    db.add(message)
    db.flush()

    return message


async def send_template_message(
    db: Session,
    *,
    organization_id: UUID,
    whatsapp_connection: WhatsAppConnection,
    customer_phone_number: str,
    template_name: str,
    language_code: str,
    parameters: list[str],
    rendered_text: str,
) -> Message:
    if not whatsapp_connection.is_active:
        raise ValueError(
            "WhatsApp connection is not active"
        )

    conversation = get_or_create_conversation(
        db,
        organization_id=organization_id,
        whatsapp_connection=whatsapp_connection,
        customer_phone_number=(
            customer_phone_number
        ),
    )

    client = MetaWhatsAppClient()

    access_token = token_encryption.decrypt(
        whatsapp_connection.access_token_encrypted
    )

    result = await client.send_template_message(
        phone_number_id=(
            whatsapp_connection.phone_number_id
        ),
        access_token=access_token,
        recipient_phone_number=(
            customer_phone_number
        ),
        template_name=template_name,
        language_code=language_code,
        parameters=parameters,
    )

    message = Message(
        conversation_id=conversation.id,
        whatsapp_message_id=result.message_id,
        sender_phone_number=(
            whatsapp_connection.display_phone_number
            or whatsapp_connection.phone_number_id
        ),
        direction="outbound",
        status="sent",
        message_type="template",
        text=rendered_text,
        whatsapp_timestamp=str(
            int(datetime.now(UTC).timestamp())
        ),
    )

    db.add(message)
    db.flush()

    return message