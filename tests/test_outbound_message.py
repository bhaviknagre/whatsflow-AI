import uuid

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    CurrentUser,
    get_current_user,
)
from app.core.encryption import token_encryption
from app.db.session import get_db
from app.main import app
from app.models.conversation import Conversation
from app.models.organization import Organization
from app.models.whatsapp_connection import (
    WhatsAppConnection,
)
from app.services import realtime as realtime_module
from app.services.messages import (
    send_outbound_message,
)
from app.services.meta_whatsapp import (
    MetaWhatsAppClient,
    WhatsAppSendResult,
)

client = TestClient(app)


@pytest.mark.asyncio
async def test_outbound_message_is_persisted_as_sent(
    db_session,
    monkeypatch,
):
    organization = Organization(
        name="Outbound Test Organization",
        slug=(
            f"outbound-test-{uuid.uuid4().hex[:8]}"
        ),
        is_active=True,
    )

    db_session.add(organization)
    db_session.flush()

    connection = WhatsAppConnection(
        organization_id=organization.id,
        waba_id="OUTBOUND_WABA",
        phone_number_id="OUTBOUND_PHONE",
        display_phone_number="+919999999999",
        verified_name="Outbound Test",
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
        customer_phone_number="919888888888",
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
        assert (
            phone_number_id
            == "OUTBOUND_PHONE"
        )

        assert (
            recipient_phone_number
            == "919888888888"
        )

        assert text == "Hello from test"

        return WhatsAppSendResult(
            message_id="wamid.OUTBOUND_TEST_001",
        )

    monkeypatch.setattr(
        MetaWhatsAppClient,
        "send_text_message",
        fake_send_text_message,
    )

    message = await send_outbound_message(
        db_session,
        organization_id=organization.id,
        conversation=conversation,
        text="Hello from test",
    )

    assert message.id is not None
    assert (
        message.whatsapp_message_id
        == "wamid.OUTBOUND_TEST_001"
    )
    assert message.direction == "outbound"
    assert message.status == "sent"
    assert message.message_type == "text"
    assert message.text == "Hello from test"
    assert (
        message.sender_phone_number
        == "+919999999999"
    )


def test_send_message_endpoint_broadcasts_message_created(
    db_session,
    monkeypatch,
):
    organization = Organization(
        name="Broadcast Test Organization",
        slug=(
            f"broadcast-test-{uuid.uuid4().hex[:8]}"
        ),
        is_active=True,
    )

    db_session.add(organization)
    db_session.flush()

    connection = WhatsAppConnection(
        organization_id=organization.id,
        waba_id="BROADCAST_WABA",
        phone_number_id="BROADCAST_PHONE",
        display_phone_number="+919999999999",
        verified_name="Broadcast Test",
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
        customer_phone_number="919888888888",
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
        return WhatsAppSendResult(
            message_id="wamid.BROADCAST_TEST_001",
        )

    monkeypatch.setattr(
        MetaWhatsAppClient,
        "send_text_message",
        fake_send_text_message,
    )

    broadcasts = []

    async def fake_broadcast_to_organization(
        self,
        organization_id,
        event,
    ):
        broadcasts.append((organization_id, event))

    monkeypatch.setattr(
        realtime_module.realtime_manager,
        "broadcast_to_organization",
        fake_broadcast_to_organization.__get__(
            realtime_module.realtime_manager
        ),
    )

    app.dependency_overrides[get_db] = (
        lambda: db_session
    )
    app.dependency_overrides[get_current_user] = (
        lambda: CurrentUser(
            user_id=uuid.uuid4(),
            organization_id=organization.id,
            role="owner",
        )
    )

    try:
        response = client.post(
            f"/api/v1/inbox/conversations/{conversation.id}/messages",
            json={"text": "Hello from test"},
        )

        assert response.status_code == 200
        assert len(broadcasts) == 1

        broadcast_org_id, event = broadcasts[0]

        assert broadcast_org_id == organization.id
        assert event["type"] == "message_created"
        assert event["conversation_id"] == str(
            conversation.id
        )
        assert (
            event["message"]["whatsapp_message_id"]
            == "wamid.BROADCAST_TEST_001"
        )
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(
            get_current_user, None
        )