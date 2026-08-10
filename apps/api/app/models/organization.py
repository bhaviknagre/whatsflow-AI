from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.whatsapp_connection import WhatsAppConnection

if TYPE_CHECKING:
    from app.models.contacts import Contact
    from app.models.user import User
    from app.models.whatsapp_connection import WhatsAppConnection

class Organization(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    Base,
):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    users: Mapped[list["User"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    whatsapp_connections: Mapped[
    list["WhatsAppConnection"]
    ] = relationship(
    back_populates="organization",
    cascade="all, delete-orphan",
    )

    contacts: Mapped[list["Contact"]] = relationship(
    back_populates="organization",
    cascade="all, delete-orphan",
    )

