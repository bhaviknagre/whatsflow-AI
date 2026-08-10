import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from app.models.message import Message
    from app.models.organization import Organization
    from app.models.whatsapp_connection import (
        WhatsAppConnection,
    )


class Conversation(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    Base,
):
    __tablename__ = "conversations"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "organizations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    whatsapp_connection_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "whatsapp_connections.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    customer_phone_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    unread_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    organization: Mapped[
        "Organization"
    ] = relationship()

    whatsapp_connection: Mapped[
        "WhatsAppConnection"
    ] = relationship()

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )