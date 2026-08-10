import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class MetaWebhookEvent(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "meta_webhook_events"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "organizations.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    waba_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    event_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    object_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )

    signature_verified: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    processing_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )