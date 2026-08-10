import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from app.models.contacts import Contact
    from app.models.organization import Organization
    from app.models.whatsapp_connection import (
        WhatsAppConnection,
    )

CAMPAIGN_STATUSES = {
    "draft",
    "scheduled",
    "running",
    "completed",
    "failed",
    "cancelled",
}

CAMPAIGN_RECIPIENT_STATUSES = {
    "pending",
    "sending",
    "sent",
    "delivered",
    "read",
    "failed",
}


class Campaign(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "campaigns"

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

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    template_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    language_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
    )

    scheduled_at: Mapped[
        datetime | None
    ] = mapped_column(
        nullable=True,
    )

    started_at: Mapped[
        datetime | None
    ] = mapped_column(
        nullable=True,
    )

    completed_at: Mapped[
        datetime | None
    ] = mapped_column(
        nullable=True,
    )

    total_recipients: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    sent_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    delivered_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    read_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    failed_count: Mapped[int] = mapped_column(
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

    recipients: Mapped[
        list["CampaignRecipient"]
    ] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
    )


class CampaignRecipient(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "campaign_recipients"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "campaigns.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    contact_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "contacts.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    phone_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    parameters: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    rendered_text: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )

    whatsapp_message_id: Mapped[
        str | None
    ] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )

    error_code: Mapped[
        str | None
    ] = mapped_column(
        String(50),
        nullable=True,
    )

    error_message: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    sent_at: Mapped[
        datetime | None
    ] = mapped_column(
        nullable=True,
    )

    delivered_at: Mapped[
        datetime | None
    ] = mapped_column(
        nullable=True,
    )

    read_at: Mapped[
        datetime | None
    ] = mapped_column(
        nullable=True,
    )

    failed_at: Mapped[
        datetime | None
    ] = mapped_column(
        nullable=True,
    )

    campaign: Mapped["Campaign"] = relationship(
        back_populates="recipients",
    )

    contact: Mapped[
        "Contact | None"
    ] = relationship()
