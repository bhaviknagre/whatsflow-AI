from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.tokens import hash_token
from app.models.refresh_session import RefreshSession


def create_refresh_session(
    db: Session,
    *,
    user_id: UUID,
    organization_id: UUID,
    refresh_token: str,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> RefreshSession:

    session = RefreshSession(
        user_id=user_id,
        organization_id=organization_id,
        token_hash=hash_token(refresh_token),
        expires_at=(
            datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        ),
        user_agent=user_agent,
        ip_address=ip_address,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


def get_active_session(
    db: Session,
    refresh_token: str,
) -> RefreshSession | None:

    token_hash = hash_token(refresh_token)

    session = db.scalar(
        select(RefreshSession).where(
            RefreshSession.token_hash == token_hash,
            RefreshSession.is_active.is_(True),
            RefreshSession.revoked_at.is_(None),
        )
    )

    if not session:
        return None

    if session.expires_at <= datetime.now(UTC):
        session.is_active = False
        db.commit()

        return None

    return session


def revoke_session(
    db: Session,
    session: RefreshSession,
) -> None:

    session.is_active = False
    session.revoked_at = datetime.now(UTC)

    db.commit()
