import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.whatsapp_connection import WhatsAppConnection


class Customer(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    Base,
):
    __tablename__ = "customers"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "organizations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    whatsapp_connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "whatsapp_connections.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    phone_number: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    display_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    profile_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    provider_customer_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    organization: Mapped["Organization"] = relationship(
        "Organization",
    )

    whatsapp_connection: Mapped[
        "WhatsAppConnection"
    ] = relationship(
        "WhatsAppConnection",
    )