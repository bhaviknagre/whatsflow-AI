from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.sessions import create_refresh_session


class AuthenticationError(Exception):
    pass


def register_user(
    db: Session,
    data: RegisterRequest,
) -> tuple[User, Organization]:

    existing_user = db.scalar(select(User).where(User.email == data.email.lower()))

    if existing_user:
        raise AuthenticationError("An account with this email already exists.")

    organization = Organization(
        name=data.organization_name,
        slug=_generate_unique_slug(
            db,
            data.organization_name,
        ),
    )

    user = User(
        email=data.email.lower(),
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        role="admin",
        organization=organization,
    )

    db.add(organization)
    db.add(user)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AuthenticationError("An account with this email already exists.") from exc

    db.refresh(user)
    db.refresh(organization)

    return user, organization


def authenticate_user(
    db: Session,
    data: LoginRequest,
) -> User:

    user = db.scalar(select(User).where(User.email == data.email.lower()))

    if not user:
        raise AuthenticationError("Invalid email or password.")

    if not verify_password(
        data.password,
        user.password_hash,
    ):
        raise AuthenticationError("Invalid email or password.")

    if not user.is_active:
        raise AuthenticationError("User account is inactive.")

    return user


def create_tokens(
    db: Session,
    user: User,
    *,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> dict[str, str]:

    access_token = create_access_token(
        user.id,
        user.organization_id,
        user.role,
    )

    refresh_token = create_refresh_token(
        user.id,
        user.organization_id,
        user.role,
    )

    create_refresh_session(
        db,
        user_id=user.id,
        organization_id=user.organization_id,
        refresh_token=refresh_token,
        user_agent=user_agent,
        ip_address=ip_address,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def _generate_unique_slug(db: Session, name: str) -> str:
    import re

    base_slug = re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")

    slug = base_slug
    suffix = 1

    while db.scalar(select(Organization).where(Organization.slug == slug)):
        suffix += 1
        slug = f"{base_slug}-{suffix}"

    return slug
