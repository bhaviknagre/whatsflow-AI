import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.meta_oauth_state import MetaOAuthState

STATE_TTL_MINUTES = 10


def create_oauth_state(
    db: Session,
    organization_id: UUID,
) -> str:
    state_value = secrets.token_urlsafe(48)

    expires_at = (
        datetime.now(UTC)
        + timedelta(minutes=STATE_TTL_MINUTES)
    )

    state = MetaOAuthState(
        organization_id=organization_id,
        state=state_value,
        expires_at=expires_at,
    )

    db.add(state)
    db.commit()

    return state_value


def consume_oauth_state(
    db: Session,
    state_value: str,
) -> UUID:
    state = db.scalar(
        select(MetaOAuthState)
        .where(
            MetaOAuthState.state == state_value
        )
        .with_for_update()
    )

    if state is None:
        raise ValueError("Invalid OAuth state")

    now = datetime.now(UTC)

    if state.used_at is not None:
        raise ValueError(
            "OAuth state has already been used"
        )

    if state.expires_at <= now:
        raise ValueError(
            "OAuth state has expired"
        )

    state.used_at = now

    db.flush()

    return state.organization_id