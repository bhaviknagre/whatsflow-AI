from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.encryption import token_encryption
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.whatsapp_connection import (
    WhatsAppConnection,
)
from app.services.meta_whatsapp import (
    MetaWhatsAppClient,
)


class WhatsAppMessageService:
    def __init__(self) -> None:
        self.client = MetaWhatsAppClient()

    def get_conversation(
        self,
        db: Session,
        *,
        organization_id: UUID,
        conversation_id: UUID,
    ) -> Conversation:
        conversation = db.scalar(
            select(Conversation)
            .where(
                Conversation.id
                == conversation_id,
                Conversation.organization_id
                == organization_id,
                Conversation.deleted_at.is_(None),
            )
        )

        if conversation is None:
            raise ValueError(
                "Conversation not found"
            )

        return conversation

    def get_connection(
        self,
        db: Session,
        *,
        organization_id: UUID,
        connection_id: UUID,
    ) -> WhatsAppConnection:
        connection = db.scalar(
            select(WhatsAppConnection)
            .where(
                WhatsAppConnection.id
                == connection_id,
                WhatsAppConnection.organization_id
                == organization_id,
                WhatsAppConnection.is_active.is_(True),
            )
        )

        if connection is None:
            raise ValueError(
                "WhatsApp connection not found"
            )

        return connection

    async def send_text(
        self,
        db: Session,
        *,
        organization_id: UUID,
        conversation_id: UUID,
        text: str,
    ) -> Message:
        conversation = self.get_conversation(
            db,
            organization_id=organization_id,
            conversation_id=conversation_id,
        )

        connection = self.get_connection(
            db,
            organization_id=organization_id,
            connection_id=(
                conversation.whatsapp_connection_id
            ),
        )

        text = text.strip()

        if not text:
            raise ValueError(
                "Message text cannot be empty"
            )

        access_token = token_encryption.decrypt(
            connection.access_token_encrypted
        )

        result = await self.client.send_text_message(
            phone_number_id=connection.phone_number_id,
            recipient_phone_number=(
                conversation.customer_phone_number
            ),
            text=text,
            access_token=access_token,
        )

        message = Message(
            conversation_id=conversation.id,
            whatsapp_message_id=result.message_id,
            sender_phone_number=(
                connection.display_phone_number
                or connection.phone_number_id
            ),
            direction="outbound",
            message_type="text",
            text=text,
            whatsapp_timestamp="pending",
            status="sent",
        )

        db.add(message)
        db.commit()
        db.refresh(message)

        return message
