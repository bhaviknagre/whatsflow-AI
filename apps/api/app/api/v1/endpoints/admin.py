from fastapi import APIRouter, Depends

from app.api.dependencies import CurrentUser
from app.core.permissions import UserRole, require_roles

router = APIRouter(tags=["Admin"])


@router.get("/admin-test")
async def admin_test(
    current_user: CurrentUser = Depends(
        require_roles(
            UserRole.OWNER,
            UserRole.ADMIN,
        )
    ),
) -> dict:
    return {"message": "Admin access granted"}
