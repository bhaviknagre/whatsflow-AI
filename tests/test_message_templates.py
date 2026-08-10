import uuid

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import CurrentUser, get_current_user
from app.core.encryption import token_encryption
from app.db.session import get_db
from app.main import app
from app.models.organization import Organization
from app.models.whatsapp_connection import (
    WhatsAppConnection,
)
from app.services.messages import (
    send_template_message,
)
from app.services.meta_whatsapp import (
    MetaWhatsAppClient,
    WhatsAppMessageTemplate,
    WhatsAppSendResult,
)

client = TestClient(app)


def create_test_connection(db_session):
    organization = Organization(
        name="Template Test Organization",
        slug=f"template-test-{uuid.uuid4().hex[:8]}",
        is_active=True,
    )

    db_session.add(organization)
    db_session.flush()

    connection = WhatsAppConnection(
        organization_id=organization.id,
        waba_id="TEMPLATE_WABA",
        phone_number_id="TEMPLATE_PHONE",
        display_phone_number="+919999999999",
        verified_name="Template Test",
        access_token_encrypted=(
            token_encryption.encrypt("test-token")
        ),
        is_active=True,
    )

    db_session.add(connection)
    db_session.flush()

    return organization, connection


@pytest.mark.asyncio
async def test_send_template_message_creates_conversation_and_message(
    db_session,
    monkeypatch,
):
    organization, connection = create_test_connection(
        db_session
    )

    async def fake_send_template_message(
        self,
        *,
        phone_number_id,
        access_token,
        recipient_phone_number,
        template_name,
        language_code,
        parameters,
    ):
        assert phone_number_id == "TEMPLATE_PHONE"
        assert recipient_phone_number == "919777777777"
        assert template_name == "sales_intro"
        assert language_code == "en_US"
        assert parameters == ["Priya"]

        return WhatsAppSendResult(
            message_id="wamid.TEMPLATE_TEST_001",
        )

    monkeypatch.setattr(
        MetaWhatsAppClient,
        "send_template_message",
        fake_send_template_message,
    )

    message = await send_template_message(
        db_session,
        organization_id=organization.id,
        whatsapp_connection=connection,
        customer_phone_number="919777777777",
        template_name="sales_intro",
        language_code="en_US",
        parameters=["Priya"],
        rendered_text="Hi Priya, this is WhatsFlow.",
    )

    assert message.id is not None
    assert (
        message.whatsapp_message_id
        == "wamid.TEMPLATE_TEST_001"
    )
    assert message.direction == "outbound"
    assert message.status == "sent"
    assert message.message_type == "template"
    assert (
        message.text
        == "Hi Priya, this is WhatsFlow."
    )
    assert message.conversation_id is not None


def test_start_conversation_creates_new_conversation(
    db_session,
    monkeypatch,
):
    organization, connection = create_test_connection(
        db_session
    )

    async def fake_get_message_templates(
        self,
        *,
        waba_id,
        access_token,
    ):
        return [
            WhatsAppMessageTemplate(
                name="sales_intro",
                language="en_US",
                category="MARKETING",
                status="APPROVED",
                body_text="Hi {{1}}, this is WhatsFlow.",
                placeholder_count=1,
            )
        ]

    async def fake_send_template_message(
        self,
        *,
        phone_number_id,
        access_token,
        recipient_phone_number,
        template_name,
        language_code,
        parameters,
    ):
        return WhatsAppSendResult(
            message_id="wamid.START_CONV_001",
        )

    monkeypatch.setattr(
        MetaWhatsAppClient,
        "get_message_templates",
        fake_get_message_templates,
    )
    monkeypatch.setattr(
        MetaWhatsAppClient,
        "send_template_message",
        fake_send_template_message,
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
            "/api/v1/inbox/conversations",
            json={
                "customer_phone_number": "+91 90000 55555",
                "template_name": "sales_intro",
                "language_code": "en_US",
                "parameters": ["Priya"],
            },
        )

        assert response.status_code == 200

        body = response.json()

        assert (
            body["customer_phone_number"]
            == "919000055555"
        )
        assert len(body["messages"]) == 1
        assert (
            body["messages"][0]["text"]
            == "Hi Priya, this is WhatsFlow."
        )
        assert (
            body["messages"][0]["message_type"]
            == "template"
        )
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(
            get_current_user, None
        )


def test_start_conversation_placeholder_mismatch_returns_400(
    db_session,
    monkeypatch,
):
    organization, connection = create_test_connection(
        db_session
    )

    async def fake_get_message_templates(
        self,
        *,
        waba_id,
        access_token,
    ):
        return [
            WhatsAppMessageTemplate(
                name="sales_intro",
                language="en_US",
                category="MARKETING",
                status="APPROVED",
                body_text="Hi {{1}}, this is WhatsFlow.",
                placeholder_count=1,
            )
        ]

    monkeypatch.setattr(
        MetaWhatsAppClient,
        "get_message_templates",
        fake_get_message_templates,
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
            "/api/v1/inbox/conversations",
            json={
                "customer_phone_number": "919000066666",
                "template_name": "sales_intro",
                "language_code": "en_US",
                "parameters": [],
            },
        )

        assert response.status_code == 400
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(
            get_current_user, None
        )
