import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.organization import Organization


class WhatsAppConnection(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "whatsapp_connections"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "organizations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    waba_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    phone_number_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    display_phone_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    verified_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    access_token_encrypted: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    expires_at: Mapped[
        datetime | None
    ] = mapped_column(
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    organization: Mapped["Organization"] = relationship(
        back_populates="whatsapp_connections",
    )