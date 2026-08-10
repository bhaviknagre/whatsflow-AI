from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import (
    CurrentUser,
    get_current_user,
)
from app.db.session import get_db
from app.schemas.contact import (
    ContactCreateRequest,
    ContactResponse,
    ContactUpdateRequest,
)
from app.services.contacts import (
    get_contact,
    get_contact_by_phone,
    get_or_create_contact,
    list_contacts,
)
from app.services.messages import normalize_phone_number

router = APIRouter(
    prefix="/contacts",
    tags=["Contacts"],
)


@router.get(
    "",
    response_model=list[ContactResponse],
)
def get_contacts(
    search: str | None = Query(default=None),
    current_user: CurrentUser = Depends(
        get_current_user,
    ),
    db: Session = Depends(get_db),
):
    return list_contacts(
        db,
        organization_id=current_user.organization_id,
        search=search,
    )


@router.post(
    "",
    response_model=ContactResponse,
    status_code=201,
)
def create_contact(
    payload: ContactCreateRequest,
    current_user: CurrentUser = Depends(
        get_current_user,
    ),
    db: Session = Depends(get_db),
):
    phone_number = normalize_phone_number(
        payload.phone_number
    )

    existing = get_contact_by_phone(
        db,
        organization_id=current_user.organization_id,
        phone_number=phone_number,
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="A contact with this phone number already exists",
        )

    contact = get_or_create_contact(
        db,
        organization_id=current_user.organization_id,
        phone_number=phone_number,
    )

    contact.name = payload.name

    db.commit()
    db.refresh(contact)

    return contact


@router.patch(
    "/{contact_id}",
    response_model=ContactResponse,
)
def update_contact(
    contact_id: UUID,
    payload: ContactUpdateRequest,
    current_user: CurrentUser = Depends(
        get_current_user,
    ),
    db: Session = Depends(get_db),
):
    contact = get_contact(
        db,
        organization_id=current_user.organization_id,
        contact_id=contact_id,
    )

    if contact is None:
        raise HTTPException(
            status_code=404,
            detail="Contact not found",
        )

    if payload.name is not None:
        contact.name = payload.name

    if payload.is_blocked is not None:
        contact.is_blocked = payload.is_blocked

    db.commit()
    db.refresh(contact)

    return contact


@router.delete(
    "/{contact_id}",
    status_code=204,
)
def delete_contact(
    contact_id: UUID,
    current_user: CurrentUser = Depends(
        get_current_user,
    ),
    db: Session = Depends(get_db),
):
    contact = get_contact(
        db,
        organization_id=current_user.organization_id,
        contact_id=contact_id,
    )

    if contact is None:
        raise HTTPException(
            status_code=404,
            detail="Contact not found",
        )

    db.delete(contact)
    db.commit()
