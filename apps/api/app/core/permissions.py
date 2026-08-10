from enum import StrEnum

from fastapi import Depends, HTTPException, status

from app.api.dependencies import (
    CurrentUser,
    get_current_user,
)


class UserRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    AGENT = "agent"
    VIEWER = "viewer"


def require_roles(
    *allowed_roles: UserRole,
):
    def dependency(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return dependency
