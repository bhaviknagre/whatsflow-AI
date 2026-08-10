import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.organization import Organization


class Contact(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "contacts"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "phone_number",
            name="uq_contacts_organization_phone",
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "organizations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    phone_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    profile_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    organization: Mapped["Organization"] = relationship(
        back_populates="contacts",
    )