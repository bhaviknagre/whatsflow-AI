from datetime import UTC, datetime
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
)
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.meta_webhook_event import (
    MetaWebhookEvent,
)
from app.models.whatsapp_connection import (
    WhatsAppConnection,
)
from app.schemas.inbox import MessageResponse
from app.services.campaigns import (
    sync_campaign_recipient_status,
)
from app.services.message_status import (
    get_message_organization_id,
    update_message_status,
)
from app.services.messages import (
    persist_incoming_message,
)
from app.services.meta_webhook import (
    parse_meta_webhook,
    persist_webhook_event,
    verify_meta_signature,
)
from app.services.meta_webhook_parser import (
    parse_whatsapp_webhook,
)
from app.services.realtime import realtime_manager

router = APIRouter(
    prefix="/meta/webhook",
    tags=["Meta Webhook"],
)


@router.get("")
def verify_webhook(
    hub_mode: str | None = Query(
        default=None,
        alias="hub.mode",
    ),
    hub_verify_token: str | None = Query(
        default=None,
        alias="hub.verify_token",
    ),
    hub_challenge: str | None = Query(
        default=None,
        alias="hub.challenge",
    ),
) -> PlainTextResponse:

    if hub_mode != "subscribe":
        raise HTTPException(
            status_code=403,
            detail="Invalid webhook mode",
        )

    if not settings.META_WEBHOOK_VERIFY_TOKEN:
        raise HTTPException(
            status_code=503,
            detail=(
                "Meta webhook verification token "
                "is not configured"
            ),
        )

    if (
        hub_verify_token
        != settings.META_WEBHOOK_VERIFY_TOKEN
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Invalid webhook verification token"
            ),
        )

    if hub_challenge is None:
        raise HTTPException(
            status_code=400,
            detail="Missing webhook challenge",
        )

    return PlainTextResponse(hub_challenge)


@router.post("")
async def receive_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> Response:
    raw_body = await request.body()

    signature = request.headers.get(
        "X-Hub-Signature-256"
    )

    if not verify_meta_signature(
        raw_body=raw_body,
        signature=signature,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature",
        )

    try:
        payload = parse_meta_webhook(raw_body)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    webhook_event, created = persist_webhook_event(
        db=db,
        raw_body=raw_body,
        payload=payload,
    )

    if (
        not created
        and webhook_event.processed_at is not None
    ):
        return Response(status_code=200)

    realtime_events: list[tuple[UUID, dict]] = []

    try:
        parsed = parse_whatsapp_webhook(payload)

        for incoming_message in parsed.messages:
            connection = db.scalar(
                select(WhatsAppConnection).where(
                    WhatsAppConnection.waba_id
                    == incoming_message.waba_id,
                    WhatsAppConnection.phone_number_id
                    == incoming_message.phone_number_id,
                    WhatsAppConnection.is_active.is_(True),
                )
            )

            if connection is None:
                continue

            persisted_message, created = (
                persist_incoming_message(
                    db,
                    organization_id=connection.organization_id,
                    whatsapp_connection=connection,
                    message=incoming_message,
                )
            )

            if not created:
                continue

            realtime_events.append(
                (
                    connection.organization_id,
                    {
                        "type": "message_created",
                        "conversation_id": str(
                            persisted_message.conversation_id
                        ),
                        "message": (
                            MessageResponse.model_validate(
                                persisted_message
                            ).model_dump(mode="json")
                        ),
                    },
                )
            )

        for status in parsed.statuses:
            message, changed = update_message_status(
                db,
                whatsapp_message_id=status.message_id,
                status=status.status,
            )

            if message is None or not changed:
                continue

            sync_campaign_recipient_status(
                db,
                message=message,
            )

            organization_id = (
                get_message_organization_id(
                    db,
                    message,
                )
            )

            if organization_id is None:
                continue

            realtime_events.append(
                (
                    organization_id,
                    {
                        "type": "message_status",
                        "message_id": (
                            message.whatsapp_message_id
                        ),
                        "conversation_id": str(
                            message.conversation_id
                        ),
                        "status": message.status,
                    },
                )
            )

        db.commit()

    except Exception as exc:
        db.rollback()

        failed_event = db.get(
            MetaWebhookEvent,
            webhook_event.id,
        )

        if failed_event is not None:
            failed_event.processing_error = (
                f"{type(exc).__name__}: {exc}"
            )
            failed_event.processed_at = None

            db.commit()

        raise HTTPException(
            status_code=500,
            detail="Webhook processing failed",
        ) from exc

    processed_event = db.get(
        MetaWebhookEvent,
        webhook_event.id,
    )

    if processed_event is not None:
        processed_event.processed_at = datetime.now(UTC)
        processed_event.processing_error = None
        db.commit()

    for organization_id, event in realtime_events:
        await realtime_manager.broadcast_to_organization(
            organization_id,
            event,
        )

    return Response(status_code=200)
