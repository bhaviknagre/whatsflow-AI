from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings

password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    try:
        return password_hasher.verify(
            password_hash,
            password,
        )
    except VerifyMismatchError:
        return False


def create_access_token(
    user_id: UUID,
    organization_id: UUID,
    role: str,
) -> str:

    now = datetime.now(UTC)

    payload = {
        "sub": str(user_id),
        "org": str(organization_id),
        "role": role,
        "type": "access",
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(
    user_id: UUID,
    organization_id: UUID,
    role: str,
) -> str:

    now = datetime.now(UTC)

    payload = {
        "sub": str(user_id),
        "org": str(organization_id),
        "role": role,
        "type": "refresh",
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict:

    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
    )
