import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from app.models.conversation import Conversation


class Message(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "messages"

    conversation_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "conversations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    whatsapp_message_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    sender_phone_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    direction: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    message_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    whatsapp_timestamp: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    conversation: Mapped[
        "Conversation"
    ] = relationship(
        back_populates="messages",
    )