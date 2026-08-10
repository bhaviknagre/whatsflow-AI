from fastapi import APIRouter

from app.api.v1.endpoints import realtime
from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.campaigns import (
    router as campaigns_router,
)
from app.api.v1.endpoints.contacts import (
    router as contacts_router,
)
from app.api.v1.endpoints.conversations import router as conversations_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.inbox import (
    router as inbox_router,
)
from app.api.v1.endpoints.meta import (
    router as meta_router,
)
from app.api.v1.endpoints.meta_webhook import (
    router as meta_webhook_router,
)
from app.api.v1.endpoints.whatsapp import (
    router as whatsapp_router,
)

router = APIRouter()

router.include_router(
    health_router,
)

router.include_router(
    auth_router,
)

router.include_router(
    admin_router,
)

router.include_router(
    conversations_router,
)

router.include_router(
    campaigns_router,
)

router.include_router(
    contacts_router,
)

router.include_router(
    whatsapp_router,
)

router.include_router(
    inbox_router,
)

router.include_router(
    meta_router,
)

router.include_router(
    meta_webhook_router,
)

router.include_router(
    realtime.router,
)
