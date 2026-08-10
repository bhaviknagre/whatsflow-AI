import uuid

from app.models.organization import Organization
from app.models.whatsapp_connection import WhatsAppConnection
from app.services.messages import persist_incoming_message
from app.services.meta_webhook_parser import (
    parse_whatsapp_webhook,
)


def test_incoming_whatsapp_message_creates_conversation_and_message(
    db_session,
):
    organization = Organization(
        name="WhatsFlow Test Organization",
        slug=f"whatsflow-test-{uuid.uuid4().hex[:8]}",
        is_active=True,
    )

    db_session.add(organization)
    db_session.flush()

    connection = WhatsAppConnection(
        organization_id=organization.id,
        waba_id="TEST_WABA_001",
        phone_number_id="TEST_PHONE_001",
        display_phone_number="+919999999999",
        verified_name="WhatsFlow Test",
        access_token_encrypted="test-token",
        is_active=True,
    )

    db_session.add(connection)
    db_session.flush()

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "TEST_WABA_001",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "metadata": {
                                "phone_number_id": (
                                    "TEST_PHONE_001"
                                ),
                            },
                            "messages": [
                                {
                                    "id": "wamid.INTEGRATION_001",
                                    "from": "919876543210",
                                    "timestamp": "1750000000",
                                    "type": "text",
                                    "text": {
                                        "body": (
                                            "Hello from WhatsFlow"
                                        ),
                                    },
                                },
                            ],
                        },
                    },
                ],
            },
        ],
    }

    parsed = parse_whatsapp_webhook(payload)

    assert len(parsed.messages) == 1

    message, created = persist_incoming_message(
        db_session,
        organization_id=organization.id,
        whatsapp_connection=connection,
        message=parsed.messages[0],
    )

    db_session.commit()

    assert created is True
    assert message.id is not None
    assert message.whatsapp_message_id == (
        "wamid.INTEGRATION_001"
    )
    assert message.sender_phone_number == (
        "919876543210"
    )
    assert message.direction == "inbound"
    assert message.message_type == "text"
    assert message.text == "Hello from WhatsFlow"
    assert message.conversation_id is not None


def test_duplicate_whatsapp_message_is_not_created(
    db_session,
):
    organization = Organization(
        name="WhatsFlow Duplicate Test",
        slug=f"duplicate-test-{uuid.uuid4().hex[:8]}",
        is_active=True,
    )

    db_session.add(organization)
    db_session.flush()

    connection = WhatsAppConnection(
        organization_id=organization.id,
        waba_id="TEST_WABA_DUPLICATE",
        phone_number_id="TEST_PHONE_DUPLICATE",
        display_phone_number="+919888888888",
        verified_name="WhatsFlow Duplicate Test",
        access_token_encrypted="test-token",
        is_active=True,
    )

    db_session.add(connection)
    db_session.flush()

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "TEST_WABA_DUPLICATE",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "metadata": {
                                "phone_number_id": (
                                    "TEST_PHONE_DUPLICATE"
                                ),
                            },
                            "messages": [
                                {
                                    "id": "wamid.DUPLICATE_001",
                                    "from": "919111111111",
                                    "timestamp": "1750000001",
                                    "type": "text",
                                    "text": {
                                        "body": "Duplicate test",
                                    },
                                },
                            ],
                        },
                    },
                ],
            },
        ],
    }

    parsed = parse_whatsapp_webhook(payload)
    incoming = parsed.messages[0]

    first, first_created = persist_incoming_message(
        db_session,
        organization_id=organization.id,
        whatsapp_connection=connection,
        message=incoming,
    )

    second, second_created = persist_incoming_message(
        db_session,
        organization_id=organization.id,
        whatsapp_connection=connection,
        message=incoming,
    )

    db_session.commit()

    assert first.id == second.id
    assert first_created is True
    assert second_created is False