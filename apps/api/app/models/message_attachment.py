import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from app.models.message import Message


class MessageAttachment(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "message_attachments"

    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "messages.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    attachment_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    mime_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    provider_media_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    filename: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    storage_key: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )

    caption: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    file_size: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    metadata_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    message: Mapped["Message"] = relationship(
        "Message",
    )