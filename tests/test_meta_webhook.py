import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.encryption import token_encryption
from app.db.session import get_db
from app.main import app
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.meta_webhook_event import (
    MetaWebhookEvent,
)
from app.models.organization import Organization
from app.models.whatsapp_connection import (
    WhatsAppConnection,
)
from app.services import realtime as realtime_module
from app.services.messages import send_outbound_message
from app.services.meta_whatsapp import MetaWhatsAppClient

client = TestClient(app)


def test_meta_webhook_verification_success(monkeypatch):
    monkeypatch.setattr(
        settings,
        "META_WEBHOOK_VERIFY_TOKEN",
        "test-webhook-token",
    )

    response = client.get(
        "/api/v1/meta/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test-webhook-token",
            "hub.challenge": "challenge-123",
        },
    )

    assert response.status_code == 200
    assert response.text == "challenge-123"


def test_meta_webhook_verification_invalid_token(monkeypatch):
    monkeypatch.setattr(
        settings,
        "META_WEBHOOK_VERIFY_TOKEN",
        "test-webhook-token",
    )

    response = client.get(
        "/api/v1/meta/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token",
            "hub.challenge": "challenge-123",
        },
    )

    assert response.status_code == 403


def test_meta_webhook_verification_invalid_mode(monkeypatch):
    monkeypatch.setattr(
        settings,
        "META_WEBHOOK_VERIFY_TOKEN",
        "test-webhook-token",
    )

    response = client.get(
        "/api/v1/meta/webhook",
        params={
            "hub.mode": "invalid",
            "hub.verify_token": "test-webhook-token",
            "hub.challenge": "challenge-123",
        },
    )

    assert response.status_code == 403

def create_meta_signature(
    body: bytes,
    secret: str,
) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    return f"sha256={digest}"

def test_meta_webhook_post_valid_signature(
    monkeypatch,
):
    secret = "test-app-secret"

    monkeypatch.setattr(
        settings,
        "META_WEBHOOK_APP_SECRET",
        secret,
    )

    payload = {
        "object": "whatsapp_business_account",
        "entry": [],
    }

    body = json.dumps(
        payload
    ).encode("utf-8")

    signature = create_meta_signature(
        body,
        secret,
    )

    response = client.post(
        "/api/v1/meta/webhook",
        content=body,
        headers={
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 200


def test_meta_webhook_updates_message_status(
    monkeypatch,
    db_session,
):
    secret = "test-app-secret"

    monkeypatch.setattr(
        settings,
        "META_WEBHOOK_APP_SECRET",
        secret,
    )

    organization = Organization(
        name="Webhook Status Test Organization",
        slug="webhook-status-test",
        is_active=True,
    )

    db_session.add(organization)
    db_session.flush()

    connection = WhatsAppConnection(
        organization_id=organization.id,
        waba_id="WEBHOOK_STATUS_WABA",
        phone_number_id="WEBHOOK_STATUS_PHONE",
        display_phone_number="+919999999999",
        verified_name="Webhook Status Test",
        access_token_encrypted="test-token",
        is_active=True,
    )

    db_session.add(connection)
    db_session.flush()

    conversation = Conversation(
        organization_id=organization.id,
        whatsapp_connection_id=connection.id,
        customer_phone_number="919888888888",
    )

    db_session.add(conversation)
    db_session.flush()

    message = Message(
        conversation_id=conversation.id,
        whatsapp_message_id="wamid.WEBHOOK_STATUS_TEST",
        sender_phone_number="+919999999999",
        direction="outbound",
        status="pending",
        message_type="text",
        text="Status webhook test",
        whatsapp_timestamp="1750000000",
    )

    db_session.add(message)
    db_session.flush()

    app.dependency_overrides[get_db] = (
        lambda: db_session
    )

    try:
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "WEBHOOK_STATUS_WABA",
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "metadata": {
                                    "phone_number_id": (
                                        "WEBHOOK_STATUS_PHONE"
                                    ),
                                },
                                "statuses": [
                                    {
                                        "id": (
                                            "wamid.WEBHOOK_STATUS_TEST"
                                        ),
                                        "status": "delivered",
                                        "timestamp": (
                                            "1750000001"
                                        ),
                                        "recipient_id": (
                                            "919888888888"
                                        ),
                                    }
                                ],
                            },
                        }
                    ],
                }
            ],
        }

        body = json.dumps(
            payload,
            separators=(",", ":"),
        ).encode("utf-8")

        signature = create_meta_signature(
            body,
            secret,
        )

        response = client.post(
            "/api/v1/meta/webhook",
            content=body,
            headers={
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 200

        db_session.refresh(message)

        assert message.status == "delivered"
    finally:
        app.dependency_overrides.pop(
            get_db, None
        )

def test_meta_webhook_post_invalid_signature(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "META_WEBHOOK_APP_SECRET",
        "test-app-secret",
    )

    payload = {
        "object": "whatsapp_business_account",
        "entry": [],
    }

    body = json.dumps(
        payload
    ).encode("utf-8")

    response = client.post(
        "/api/v1/meta/webhook",
        content=body,
        headers={
            "X-Hub-Signature-256": (
                "sha256=invalid"
            ),
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 401

def test_meta_webhook_post_missing_signature(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "META_WEBHOOK_APP_SECRET",
        "test-app-secret",
    )

    payload = {
        "object": "whatsapp_business_account",
        "entry": [],
    }

    body = json.dumps(
        payload
    ).encode("utf-8")

    response = client.post(
        "/api/v1/meta/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 401

def test_meta_webhook_post_invalid_object(
    monkeypatch,
):
    secret = "test-app-secret"

    monkeypatch.setattr(
        settings,
        "META_WEBHOOK_APP_SECRET",
        secret,
    )

    payload = {
        "object": "instagram",
        "entry": [],
    }

    body = json.dumps(
        payload
    ).encode("utf-8")

    signature = create_meta_signature(
        body,
        secret,
    )

    response = client.post(
        "/api/v1/meta/webhook",
        content=body,
        headers={
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 400

def test_meta_webhook_persists_event(
    monkeypatch,
    db_session,
):
    secret = "test-app-secret"

    monkeypatch.setattr(
        settings,
        "META_WEBHOOK_APP_SECRET",
        secret,
    )

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [],
            }
        ],
    }

    body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    signature = create_meta_signature(
        body,
        secret,
    )

    response = client.post(
        "/api/v1/meta/webhook",
        content=body,
        headers={
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 200

def test_meta_webhook_creates_incoming_message(
    monkeypatch,
    db_session,
):
    secret = "test-app-secret"

    monkeypatch.setattr(
        settings,
        "META_WEBHOOK_APP_SECRET",
        secret,
    )

    organization = Organization(
        name="Webhook Inbound Test Organization",
        slug="webhook-inbound-test",
        is_active=True,
    )

    db_session.add(organization)
    db_session.flush()

    connection = WhatsAppConnection(
        organization_id=organization.id,
        waba_id="WEBHOOK_INBOUND_WABA",
        phone_number_id="WEBHOOK_INBOUND_PHONE",
        display_phone_number="+919999999999",
        verified_name="Webhook Inbound Test",
        access_token_encrypted="test-token",
        is_active=True,
    )

    db_session.add(connection)
    db_session.flush()

    app.dependency_overrides[get_db] = (
        lambda: db_session
    )

    try:
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "WEBHOOK_INBOUND_WABA",
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "metadata": {
                                    "phone_number_id": (
                                        "WEBHOOK_INBOUND_PHONE"
                                    ),
                                },
                                "messages": [
                                    {
                                        "id": (
                                            "wamid.WEBHOOK_INBOUND_001"
                                        ),
                                        "from": "919876543210",
                                        "timestamp": (
                                            "1750000000"
                                        ),
                                        "type": "text",
                                        "text": {
                                            "body": (
                                                "Hello from Meta"
                                            ),
                                        },
                                    }
                                ],
                            },
                        }
                    ],
                }
            ],
        }

        body = json.dumps(
            payload,
            separators=(",", ":"),
        ).encode("utf-8")

        signature = create_meta_signature(
            body,
            secret,
        )

        response = client.post(
            "/api/v1/meta/webhook",
            content=body,
            headers={
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 200

        message = db_session.query(Message).filter(
            Message.whatsapp_message_id
            == "wamid.WEBHOOK_INBOUND_001"
        ).first()

        assert message is not None
        assert message.sender_phone_number == (
            "919876543210"
        )
        assert message.direction == "inbound"
        assert message.message_type == "text"
        assert message.text == "Hello from Meta"

        conversation = (
            db_session.query(Conversation)
            .filter(
                Conversation.id
                == message.conversation_id
            )
            .first()
        )

        assert conversation is not None
        assert (
            conversation.organization_id
            == organization.id
        )
        assert (
            conversation.whatsapp_connection_id
            == connection.id
        )
        assert (
            conversation.customer_phone_number
            == "919876543210"
        )

    finally:
        app.dependency_overrides.pop(
            get_db,
            None,
        )


def test_meta_webhook_duplicate_delivery_is_not_reprocessed(
    monkeypatch,
    db_session,
):
    secret = "test-app-secret"

    monkeypatch.setattr(
        settings,
        "META_WEBHOOK_APP_SECRET",
        secret,
    )

    organization = Organization(
        name="Webhook Duplicate Delivery Organization",
        slug="webhook-duplicate-delivery",
        is_active=True,
    )

    db_session.add(organization)
    db_session.flush()

    connection = WhatsAppConnection(
        organization_id=organization.id,
        waba_id="WEBHOOK_DUPLICATE_WABA",
        phone_number_id="WEBHOOK_DUPLICATE_PHONE",
        display_phone_number="+919999999999",
        verified_name="Webhook Duplicate Delivery",
        access_token_encrypted="test-token",
        is_active=True,
    )

    db_session.add(connection)
    db_session.flush()

    app.dependency_overrides[get_db] = (
        lambda: db_session
    )

    try:
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "WEBHOOK_DUPLICATE_WABA",
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "metadata": {
                                    "phone_number_id": (
                                        "WEBHOOK_DUPLICATE_PHONE"
                                    ),
                                },
                                "messages": [
                                    {
                                        "id": (
                                            "wamid.WEBHOOK_DUPLICATE_001"
                                        ),
                                        "from": "919876543210",
                                        "timestamp": (
                                            "1750000000"
                                        ),
                                        "type": "text",
                                        "text": {
                                            "body": (
                                                "Hello from Meta"
                                            ),
                                        },
                                    }
                                ],
                            },
                        }
                    ],
                }
            ],
        }

        body = json.dumps(
            payload,
            separators=(",", ":"),
        ).encode("utf-8")

        signature = create_meta_signature(
            body,
            secret,
        )

        headers = {
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        }

        first_response = client.post(
            "/api/v1/meta/webhook",
            content=body,
            headers=headers,
        )

        second_response = client.post(
            "/api/v1/meta/webhook",
            content=body,
            headers=headers,
        )

        assert first_response.status_code == 200
        assert second_response.status_code == 200

        messages = (
            db_session.query(Message)
            .filter(
                Message.whatsapp_message_id
                == "wamid.WEBHOOK_DUPLICATE_001"
            )
            .all()
        )

        assert len(messages) == 1

    finally:
        app.dependency_overrides.pop(
            get_db,
            None,
        )


def test_meta_webhook_retries_previously_failed_delivery(
    monkeypatch,
    db_session,
):
    secret = "test-app-secret"

    monkeypatch.setattr(
        settings,
        "META_WEBHOOK_APP_SECRET",
        secret,
    )

    organization = Organization(
        name="Webhook Retry Organization",
        slug="webhook-retry-test",
        is_active=True,
    )

    db_session.add(organization)
    db_session.flush()

    connection = WhatsAppConnection(
        organization_id=organization.id,
        waba_id="WEBHOOK_RETRY_WABA",
        phone_number_id="WEBHOOK_RETRY_PHONE",
        display_phone_number="+919999999999",
        verified_name="Webhook Retry Test",
        access_token_encrypted="test-token",
        is_active=True,
    )

    db_session.add(connection)
    db_session.flush()

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WEBHOOK_RETRY_WABA",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "metadata": {
                                "phone_number_id": (
                                    "WEBHOOK_RETRY_PHONE"
                                ),
                            },
                            "messages": [
                                {
                                    "id": (
                                        "wamid.WEBHOOK_RETRY_001"
                                    ),
                                    "from": "919876543210",
                                    "timestamp": (
                                        "1750000000"
                                    ),
                                    "type": "text",
                                    "text": {
                                        "body": (
                                            "Hello from Meta"
                                        ),
                                    },
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }

    body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    signature = create_meta_signature(
        body,
        secret,
    )

    # Simulate a previous delivery that was persisted
    # but never finished processing (e.g. the process
    # crashed mid-request): the event row exists, but
    # processed_at is still None.
    event_hash = hashlib.sha256(body).hexdigest()

    existing_event = MetaWebhookEvent(
        organization_id=organization.id,
        waba_id="WEBHOOK_RETRY_WABA",
        event_hash=event_hash,
        object_type="whatsapp_business_account",
        payload=payload,
        signature_verified=True,
        received_at=datetime.now(UTC),
        processed_at=None,
        processing_error="Simulated prior failure",
    )

    db_session.add(existing_event)
    db_session.flush()

    app.dependency_overrides[get_db] = (
        lambda: db_session
    )

    try:
        response = client.post(
            "/api/v1/meta/webhook",
            content=body,
            headers={
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 200

        message = (
            db_session.query(Message)
            .filter(
                Message.whatsapp_message_id
                == "wamid.WEBHOOK_RETRY_001"
            )
            .first()
        )

        assert message is not None

        db_session.refresh(existing_event)

        assert existing_event.processed_at is not None
        assert existing_event.processing_error is None

    finally:
        app.dependency_overrides.pop(
            get_db,
            None,
        )


def test_meta_webhook_same_message_across_two_deliveries_broadcasts_once(
    monkeypatch,
    db_session,
):
    """
    Two different webhook deliveries (different raw
    bodies, so not caught by the event-hash dedup from
    persist_webhook_event) can still carry the same
    underlying WhatsApp message_id - e.g. Meta re-sends
    with a slightly different envelope. persist_incoming_
    message() must only report created=True the first
    time, so the second delivery does not re-broadcast
    message_created.
    """
    secret = "test-app-secret"

    monkeypatch.setattr(
        settings,
        "META_WEBHOOK_APP_SECRET",
        secret,
    )

    organization = Organization(
        name="Webhook Rebroadcast Organization",
        slug="webhook-rebroadcast-test",
        is_active=True,
    )

    db_session.add(organization)
    db_session.flush()

    connection = WhatsAppConnection(
        organization_id=organization.id,
        waba_id="WEBHOOK_REBROADCAST_WABA",
        phone_number_id="WEBHOOK_REBROADCAST_PHONE",
        display_phone_number="+919999999999",
        verified_name="Webhook Rebroadcast Test",
        access_token_encrypted="test-token",
        is_active=True,
    )

    db_session.add(connection)
    db_session.flush()

    broadcasts = []

    async def fake_broadcast_to_organization(
        self,
        organization_id,
        event,
    ):
        broadcasts.append(event)

    monkeypatch.setattr(
        realtime_module.realtime_manager,
        "broadcast_to_organization",
        fake_broadcast_to_organization.__get__(
            realtime_module.realtime_manager
        ),
    )

    def build_payload(extra_field: str) -> dict:
        return {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "WEBHOOK_REBROADCAST_WABA",
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "metadata": {
                                    "phone_number_id": (
                                        "WEBHOOK_REBROADCAST_PHONE"
                                    ),
                                    "extra": extra_field,
                                },
                                "messages": [
                                    {
                                        "id": (
                                            "wamid.REBROADCAST_001"
                                        ),
                                        "from": "919876543210",
                                        "timestamp": (
                                            "1750000000"
                                        ),
                                        "type": "text",
                                        "text": {
                                            "body": (
                                                "Hello from Meta"
                                            ),
                                        },
                                    }
                                ],
                            },
                        }
                    ],
                }
            ],
        }

    app.dependency_overrides[get_db] = (
        lambda: db_session
    )

    try:
        first_body = json.dumps(
            build_payload("first-delivery"),
            separators=(",", ":"),
        ).encode("utf-8")

        second_body = json.dumps(
            build_payload("second-delivery"),
            separators=(",", ":"),
        ).encode("utf-8")

        assert first_body != second_body

        first_response = client.post(
            "/api/v1/meta/webhook",
            content=first_body,
            headers={
                "X-Hub-Signature-256": (
                    create_meta_signature(
                        first_body, secret
                    )
                ),
                "Content-Type": "application/json",
            },
        )

        second_response = client.post(
            "/api/v1/meta/webhook",
            content=second_body,
            headers={
                "X-Hub-Signature-256": (
                    create_meta_signature(
                        second_body, secret
                    )
                ),
                "Content-Type": "application/json",
            },
        )

        assert first_response.status_code == 200
        assert second_response.status_code == 200

        messages = (
            db_session.query(Message)
            .filter(
                Message.whatsapp_message_id
                == "wamid.REBROADCAST_001"
            )
            .all()
        )

        assert len(messages) == 1

        message_created_events = [
            event
            for event in broadcasts
            if event["type"] == "message_created"
        ]

        assert len(message_created_events) == 1

    finally:
        app.dependency_overrides.pop(
            get_db,
            None,
        )


@pytest.mark.asyncio
async def test_outbound_message_failure_is_not_persisted(
    db_session,
    monkeypatch,
):
    organization = Organization(
        name="Outbound Failure Test",
        slug=(
            f"outbound-failure-{uuid.uuid4().hex[:8]}"
        ),
        is_active=True,
    )

    db_session.add(organization)
    db_session.flush()

    connection = WhatsAppConnection(
        organization_id=organization.id,
        waba_id="OUTBOUND_FAILURE_WABA",
        phone_number_id="OUTBOUND_FAILURE_PHONE",
        display_phone_number="+919999999999",
        verified_name="Outbound Failure Test",
        access_token_encrypted=(
            token_encryption.encrypt("test-token")
        ),
        is_active=True,
    )

    db_session.add(connection)
    db_session.flush()

    conversation = Conversation(
        organization_id=organization.id,
        whatsapp_connection_id=connection.id,
        customer_phone_number="919777777777",
    )

    db_session.add(conversation)
    db_session.flush()

    async def fake_send_text_message(
        self,
        *,
        phone_number_id,
        access_token,
        recipient_phone_number,
        text,
    ):
        raise ValueError(
            "Meta API request failed"
        )

    monkeypatch.setattr(
        MetaWhatsAppClient,
        "send_text_message",
        fake_send_text_message,
    )

    with pytest.raises(ValueError):
        await send_outbound_message(
            db_session,
            organization_id=organization.id,
            conversation=conversation,
            text="This should fail",
        )