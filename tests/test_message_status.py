import uuid

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.organization import Organization
from app.models.whatsapp_connection import (
    WhatsAppConnection,
)
from app.services.message_status import (
    update_message_status,
)


def create_test_message(db_session):
    organization = Organization(
        name="Status Test Organization",
        slug=f"status-test-{uuid.uuid4().hex[:8]}",
        is_active=True,
    )

    db_session.add(organization)
    db_session.flush()

    connection = WhatsAppConnection(
        organization_id=organization.id,
        waba_id="STATUS_WABA",
        phone_number_id="STATUS_PHONE",
        display_phone_number="+919999999999",
        verified_name="Status Test",
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
        whatsapp_message_id="wamid.STATUS_TEST",
        sender_phone_number="919888888888",
        direction="outbound",
        status="pending",
        message_type="text",
        text="Status test",
        whatsapp_timestamp="1750000000",
    )

    db_session.add(message)
    db_session.flush()

    return message


def test_message_status_progression(
    db_session,
):
    message = create_test_message(
        db_session
    )

    _, changed = update_message_status(
        db_session,
        whatsapp_message_id=(
            "wamid.STATUS_TEST"
        ),
        status="sent",
    )

    assert message.status == "sent"
    assert changed is True

    _, changed = update_message_status(
        db_session,
        whatsapp_message_id=(
            "wamid.STATUS_TEST"
        ),
        status="delivered",
    )

    assert message.status == "delivered"
    assert changed is True

    _, changed = update_message_status(
        db_session,
        whatsapp_message_id=(
            "wamid.STATUS_TEST"
        ),
        status="read",
    )

    assert message.status == "read"
    assert changed is True


def test_message_status_repeat_is_not_changed(
    db_session,
):
    create_test_message(db_session)

    update_message_status(
        db_session,
        whatsapp_message_id=(
            "wamid.STATUS_TEST"
        ),
        status="delivered",
    )

    _, changed = update_message_status(
        db_session,
        whatsapp_message_id=(
            "wamid.STATUS_TEST"
        ),
        status="delivered",
    )

    assert changed is False


def test_message_status_cannot_downgrade(
    db_session,
):
    message = create_test_message(
        db_session
    )

    message.status = "read"

    _, changed = update_message_status(
        db_session,
        whatsapp_message_id=(
            "wamid.STATUS_TEST"
        ),
        status="delivered",
    )

    assert message.status == "read"
    assert changed is False


def test_unknown_message_status_is_ignored(
    db_session,
):
    result, changed = update_message_status(
        db_session,
        whatsapp_message_id=(
            "wamid.DOES_NOT_EXIST"
        ),
        status="delivered",
    )

    assert result is None
    assert changed is False
