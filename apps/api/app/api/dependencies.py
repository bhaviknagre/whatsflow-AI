from dataclasses import dataclass
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from app.core.security import decode_token

security = HTTPBearer()


@dataclass(frozen=True)
class CurrentUser:
    user_id: UUID
    organization_id: UUID
    role: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:

    try:
        payload = decode_token(credentials.credentials)

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=401,
                detail="Invalid access token",
            )

        return CurrentUser(
            user_id=UUID(payload["sub"]),
            organization_id=UUID(payload["org"]),
            role=payload["role"],
        )

    except (
        jwt.InvalidTokenError,
        KeyError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        ) from exc
