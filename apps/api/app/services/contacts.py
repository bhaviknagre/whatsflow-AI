import re
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.contacts import Contact

_NON_DIGIT_PATTERN = re.compile(r"\D")


def normalize_phone_number(value: str) -> str:
    return _NON_DIGIT_PATTERN.sub("", value)


def get_contact(
    db: Session,
    *,
    organization_id: UUID,
    contact_id: UUID,
) -> Contact | None:
    return db.scalar(
        select(Contact).where(
            Contact.id == contact_id,
            Contact.organization_id == organization_id,
        )
    )


def get_contact_by_phone(
    db: Session,
    *,
    organization_id: UUID,
    phone_number: str,
) -> Contact | None:
    phone_number = normalize_phone_number(phone_number)

    return db.scalar(
        select(Contact).where(
            Contact.organization_id == organization_id,
            Contact.phone_number == phone_number,
        )
    )


def get_or_create_contact(
    db: Session,
    *,
    organization_id: UUID,
    phone_number: str,
    profile_name: str | None = None,
) -> Contact:
    phone_number = normalize_phone_number(phone_number)

    contact = get_contact_by_phone(
        db,
        organization_id=organization_id,
        phone_number=phone_number,
    )

    if contact is not None:
        if (
            profile_name
            and contact.profile_name != profile_name
        ):
            contact.profile_name = profile_name
            db.flush()

        return contact

    contact = Contact(
        organization_id=organization_id,
        phone_number=phone_number,
        profile_name=profile_name,
        is_blocked=False,
    )

    db.add(contact)
    db.flush()

    return contact


def list_contacts(
    db: Session,
    *,
    organization_id: UUID,
    search: str | None = None,
) -> list[Contact]:
    query = select(Contact).where(
        Contact.organization_id == organization_id,
    )

    if search:
        pattern = f"%{search.strip()}%"

        query = query.where(
            or_(
                Contact.name.ilike(pattern),
                Contact.profile_name.ilike(pattern),
                Contact.phone_number.ilike(pattern),
            )
        )

    return list(
        db.scalars(
            query.order_by(Contact.created_at.desc())
        ).all()
    )
