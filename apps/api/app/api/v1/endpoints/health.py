from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser, get_current_user
from app.db.session import get_db
from app.services.health import check_database

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health(db: Session = Depends(get_db)) -> dict:
    database_healthy = check_database(db)

    return {
        "status": "healthy",
        "services": {
            "api": "healthy",
            "database": "healthy" if database_healthy else "unhealthy",
        },
    }


@router.get("/health/protected")
async def protected_health(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    return {
        "status": "healthy",
        "user_id": str(current_user.user_id),
        "organization_id": str(current_user.organization_id),
    }
