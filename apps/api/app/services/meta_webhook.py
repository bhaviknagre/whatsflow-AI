import hashlib
import hmac
import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.meta_webhook_event import MetaWebhookEvent
from app.models.whatsapp_connection import WhatsAppConnection


def verify_meta_signature(
    *,
    raw_body: bytes,
    signature: str | None,
) -> bool:
    """
    Verify Meta's X-Hub-Signature-256 header.
    """

    if not signature:
        return False

    if not settings.META_WEBHOOK_APP_SECRET:
        return False

    prefix = "sha256="

    if not signature.startswith(prefix):
        return False

    received_signature = signature[len(prefix):]

    expected_signature = hmac.new(
        settings.META_WEBHOOK_APP_SECRET.encode(
            "utf-8"
        ),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        received_signature,
        expected_signature,
    )


def parse_meta_webhook(
    raw_body: bytes,
) -> dict[str, Any]:
    """
    Parse and validate the basic Meta webhook envelope.
    """

    try:
        payload = json.loads(
            raw_body.decode("utf-8")
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise ValueError(
            "Invalid webhook JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise ValueError(
            "Webhook payload must be an object"
        )

    if payload.get("object") != "whatsapp_business_account":
        raise ValueError(
            "Unsupported Meta webhook object"
        )

    return payload


def calculate_event_hash(
    raw_body: bytes,
) -> str:
    return hashlib.sha256(
        raw_body
    ).hexdigest()


def extract_waba_id(
    payload: dict[str, Any],
) -> str | None:
    """
    Extract the WhatsApp Business Account ID
    from the Meta webhook envelope.
    """

    entries = payload.get("entry")

    if not isinstance(entries, list):
        return None

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        waba_id = entry.get("id")

        if isinstance(waba_id, str) and waba_id:
            return waba_id

    return None


def persist_webhook_event(
    *,
    db: Session,
    raw_body: bytes,
    payload: dict[str, Any],
) -> tuple[MetaWebhookEvent, bool]:
    """
    Persist a verified Meta webhook.

    Returns:
        (event, created)

    created=False means the exact webhook body
    has already been received.
    """

    event_hash = calculate_event_hash(
        raw_body
    )

    existing_event = db.scalar(
        select(MetaWebhookEvent).where(
            MetaWebhookEvent.event_hash
            == event_hash
        )
    )

    if existing_event is not None:
        return existing_event, False

    waba_id = extract_waba_id(payload)

    organization_id = None

    if waba_id:
        connection = db.scalar(
            select(WhatsAppConnection).where(
                WhatsAppConnection.waba_id
                == waba_id,
                WhatsAppConnection.is_active.is_(True),
            )
        )

        if connection is not None:
            organization_id = (
                connection.organization_id
            )

    event = MetaWebhookEvent(
        organization_id=organization_id,
        waba_id=waba_id,
        event_hash=event_hash,
        object_type=payload["object"],
        payload=payload,
        signature_verified=True,
        received_at=datetime.now(UTC),
    )

    db.add(event)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        existing_event = db.scalar(
            select(MetaWebhookEvent).where(
                MetaWebhookEvent.event_hash
                == event_hash
            )
        )

        if existing_event is None:
            raise

        return existing_event, False

    db.refresh(event)

    return event, True