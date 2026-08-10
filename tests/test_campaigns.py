import uuid

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.dependencies import CurrentUser, get_current_user
from app.core.encryption import token_encryption
from app.db.session import get_db
from app.main import app
from app.models.campaign import Campaign, CampaignRecipient
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.organization import Organization
from app.models.whatsapp_connection import (
    WhatsAppConnection,
)
from app.services.meta_whatsapp import (
    MetaWhatsAppClient,
    WhatsAppMessageTemplate,
    WhatsAppSendResult,
)

client = TestClient(app)


def create_test_connection(
    db_session,
    *,
    is_active: bool = True,
):
    organization = Organization(
        name="Campaign Test Organization",
        slug=f"campaign-test-{uuid.uuid4().hex[:8]}",
        is_active=True,
    )

    db_session.add(organization)
    db_session.flush()

    connection = WhatsAppConnection(
        organization_id=organization.id,
        waba_id=f"CAMPAIGN_WABA_{uuid.uuid4().hex[:8]}",
        phone_number_id=(
            f"CAMPAIGN_PHONE_{uuid.uuid4().hex[:8]}"
        ),
        display_phone_number="+919999999999",
        verified_name="Campaign Test",
        access_token_encrypted=(
            token_encryption.encrypt("test-token")
        ),
        is_active=is_active,
    )

    db_session.add(connection)
    db_session.flush()

    return organization, connection


def override_auth(db_session, organization):
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


def clear_auth():
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(
        get_current_user, None
    )


async def fake_get_message_templates(
    self,
    *,
    waba_id,
    access_token,
):
    return [
        WhatsAppMessageTemplate(
            name="promo",
            language="en_US",
            category="MARKETING",
            status="APPROVED",
            body_text="Hi {{1}}, special offer!",
            placeholder_count=1,
        )
    ]


def create_campaign_payload(recipients):
    return {
        "name": "August Promo",
        "template_name": "promo",
        "language_code": "en_US",
        "recipients": recipients,
    }


def test_create_campaign(db_session, monkeypatch):
    organization, connection = (
        create_test_connection(db_session)
    )

    monkeypatch.setattr(
        MetaWhatsAppClient,
        "get_message_templates",
        fake_get_message_templates,
    )

    override_auth(db_session, organization)

    try:
        response = client.post(
            "/api/v1/campaigns",
            json=create_campaign_payload(
                [
                    {
                        "phone_number": (
                            "919000011111"
                        ),
                        "parameters": ["Ravi"],
                    },
                    {
                        "phone_number": (
                            "919000022222"
                        ),
                        "parameters": ["Priya"],
                    },
                ]
            ),
        )

        assert response.status_code == 200

        body = response.json()

        assert body["status"] == "draft"
        assert body["total_recipients"] == 2
        assert len(body["recipients"]) == 2

        campaign = db_session.scalar(
            select(Campaign).where(
                Campaign.id == body["id"]
            )
        )

        assert campaign is not None
        assert campaign.name == "August Promo"

        recipients = db_session.scalars(
            select(CampaignRecipient).where(
                CampaignRecipient.campaign_id
                == campaign.id
            )
        ).all()

        assert len(recipients) == 2
        assert all(
            recipient.status == "pending"
            for recipient in recipients
        )
    finally:
        clear_auth()


def test_create_campaign_requires_approved_template(
    db_session, monkeypatch
):
    organization, connection = (
        create_test_connection(db_session)
    )

    monkeypatch.setattr(
        MetaWhatsAppClient,
        "get_message_templates",
        fake_get_message_templates,
    )

    override_auth(db_session, organization)

    try:
        response = client.post(
            "/api/v1/campaigns",
            json=create_campaign_payload(
                [
                    {
                        "phone_number": (
                            "919000011111"
                        ),
                        "parameters": ["Ravi"],
                    }
                ]
            )
            | {"template_name": "not_a_real_template"},
        )

        assert response.status_code == 400
    finally:
        clear_auth()


def test_create_campaign_rejects_inactive_connection(
    db_session, monkeypatch
):
    organization, connection = (
        create_test_connection(
            db_session, is_active=False
        )
    )

    monkeypatch.setattr(
        MetaWhatsAppClient,
        "get_message_templates",
        fake_get_message_templates,
    )

    override_auth(db_session, organization)

    try:
        response = client.post(
            "/api/v1/campaigns",
            json=create_campaign_payload(
                [
                    {
                        "phone_number": (
                            "919000011111"
                        ),
                        "parameters": ["Ravi"],
                    }
                ]
            ),
        )

        assert response.status_code == 409
    finally:
        clear_auth()


def test_create_campaign_snapshots_recipients(
    db_session, monkeypatch
):
    organization, connection = (
        create_test_connection(db_session)
    )

    monkeypatch.setattr(
        MetaWhatsAppClient,
        "get_message_templates",
        fake_get_message_templates,
    )

    override_auth(db_session, organization)

    try:
        response = client.post(
            "/api/v1/campaigns",
            json=create_campaign_payload(
                [
                    {
                        "phone_number": (
                            "919000011111"
                        ),
                        "parameters": ["Ravi"],
                    }
                ]
            ),
        )

        assert response.status_code == 200

        body = response.json()

        assert (
            body["recipients"][0]["rendered_text"]
            == "Hi Ravi, special offer!"
        )
    finally:
        clear_auth()


def _create_campaign_via_api(
    db_session, monkeypatch, *, recipients
):
    organization, connection = (
        create_test_connection(db_session)
    )

    monkeypatch.setattr(
        MetaWhatsAppClient,
        "get_message_templates",
        fake_get_message_templates,
    )

    override_auth(db_session, organization)

    response = client.post(
        "/api/v1/campaigns",
        json=create_campaign_payload(recipients),
    )

    assert response.status_code == 200

    return organization, connection, response.json()


def test_send_campaign(db_session, monkeypatch):
    organization, connection, campaign_body = (
        _create_campaign_via_api(
            db_session,
            monkeypatch,
            recipients=[
                {
                    "phone_number": "919000011111",
                    "parameters": ["Ravi"],
                },
                {
                    "phone_number": "919000022222",
                    "parameters": ["Priya"],
                },
            ],
        )
    )

    try:

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
                message_id=(
                    f"wamid.{recipient_phone_number}"
                ),
            )

        monkeypatch.setattr(
            MetaWhatsAppClient,
            "send_template_message",
            fake_send_template_message,
        )

        response = client.post(
            "/api/v1/campaigns/"
            f"{campaign_body['id']}/send",
        )

        assert response.status_code == 200

        body = response.json()

        assert body["status"] == "completed"
        assert body["sent_count"] == 2
        assert body["failed_count"] == 0
    finally:
        clear_auth()


def test_campaign_failed_recipient_does_not_stop_campaign(
    db_session, monkeypatch
):
    failing_phone_number = "919000022222"

    organization, connection, campaign_body = (
        _create_campaign_via_api(
            db_session,
            monkeypatch,
            recipients=[
                {
                    "phone_number": "919000011111",
                    "parameters": ["Ravi"],
                },
                {
                    "phone_number": (
                        failing_phone_number
                    ),
                    "parameters": ["Priya"],
                },
                {
                    "phone_number": "919000033333",
                    "parameters": ["Aman"],
                },
            ],
        )
    )

    try:

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
            if (
                recipient_phone_number
                == failing_phone_number
            ):
                request = httpx.Request(
                    "POST",
                    "https://graph.facebook.com/fake",
                )
                response = httpx.Response(
                    status_code=400,
                    request=request,
                    json={
                        "error": {
                            "message": (
                                "Invalid phone number"
                            )
                        }
                    },
                )

                raise httpx.HTTPStatusError(
                    "Bad request",
                    request=request,
                    response=response,
                )

            return WhatsAppSendResult(
                message_id=(
                    f"wamid.{recipient_phone_number}"
                ),
            )

        monkeypatch.setattr(
            MetaWhatsAppClient,
            "send_template_message",
            fake_send_template_message,
        )

        response = client.post(
            "/api/v1/campaigns/"
            f"{campaign_body['id']}/send",
        )

        assert response.status_code == 200

        body = response.json()

        assert body["status"] == "completed"
        assert body["sent_count"] == 2
        assert body["failed_count"] == 1

        recipients = {
            recipient["phone_number"]: recipient
            for recipient in body["recipients"]
        }

        assert (
            recipients[failing_phone_number][
                "status"
            ]
            == "failed"
        )
        assert (
            recipients["919000011111"]["status"]
            == "sent"
        )
        assert (
            recipients["919000033333"]["status"]
            == "sent"
        )
    finally:
        clear_auth()


def test_campaign_status_completed(
    db_session, monkeypatch
):
    organization, connection, campaign_body = (
        _create_campaign_via_api(
            db_session,
            monkeypatch,
            recipients=[
                {
                    "phone_number": "919000011111",
                    "parameters": ["Ravi"],
                }
            ],
        )
    )

    try:

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
                message_id=(
                    f"wamid.{recipient_phone_number}"
                ),
            )

        monkeypatch.setattr(
            MetaWhatsAppClient,
            "send_template_message",
            fake_send_template_message,
        )

        response = client.post(
            "/api/v1/campaigns/"
            f"{campaign_body['id']}/send",
        )

        assert response.status_code == 200

        body = response.json()

        assert body["status"] == "completed"
        assert body["completed_at"] is not None
    finally:
        clear_auth()


def test_duplicate_campaign_send_is_rejected(
    db_session, monkeypatch
):
    organization, connection, campaign_body = (
        _create_campaign_via_api(
            db_session,
            monkeypatch,
            recipients=[
                {
                    "phone_number": "919000011111",
                    "parameters": ["Ravi"],
                }
            ],
        )
    )

    try:

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
                message_id=(
                    f"wamid.{recipient_phone_number}"
                ),
            )

        monkeypatch.setattr(
            MetaWhatsAppClient,
            "send_template_message",
            fake_send_template_message,
        )

        first_response = client.post(
            "/api/v1/campaigns/"
            f"{campaign_body['id']}/send",
        )

        second_response = client.post(
            "/api/v1/campaigns/"
            f"{campaign_body['id']}/send",
        )

        assert first_response.status_code == 200
        assert second_response.status_code == 409
    finally:
        clear_auth()


def test_cancel_campaign(db_session, monkeypatch):
    organization, connection, campaign_body = (
        _create_campaign_via_api(
            db_session,
            monkeypatch,
            recipients=[
                {
                    "phone_number": "919000011111",
                    "parameters": ["Ravi"],
                }
            ],
        )
    )

    try:
        response = client.post(
            "/api/v1/campaigns/"
            f"{campaign_body['id']}/cancel",
        )

        assert response.status_code == 200

        body = response.json()

        assert body["status"] == "cancelled"
    finally:
        clear_auth()


def test_campaign_message_status_updates_recipient(
    db_session, monkeypatch
):
    import hashlib
    import hmac
    import json

    from app.core.config import settings

    organization, connection, campaign_body = (
        _create_campaign_via_api(
            db_session,
            monkeypatch,
            recipients=[
                {
                    "phone_number": "919888888888",
                    "parameters": ["Ravi"],
                }
            ],
        )
    )

    try:
        recipient = db_session.scalar(
            select(CampaignRecipient).where(
                CampaignRecipient.campaign_id
                == campaign_body["id"]
            )
        )

        conversation = Conversation(
            organization_id=organization.id,
            whatsapp_connection_id=connection.id,
            customer_phone_number="919888888888",
        )

        db_session.add(conversation)
        db_session.flush()

        message = Message(
            conversation_id=conversation.id,
            whatsapp_message_id=(
                "wamid.CAMPAIGN_STATUS_TEST"
            ),
            sender_phone_number="+919999999999",
            direction="outbound",
            status="sent",
            message_type="template",
            text="Hi Ravi, special offer!",
            whatsapp_timestamp="1750000000",
        )

        db_session.add(message)
        db_session.flush()

        recipient.whatsapp_message_id = (
            "wamid.CAMPAIGN_STATUS_TEST"
        )
        recipient.status = "sent"

        db_session.commit()

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
                    "id": connection.waba_id,
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "metadata": {
                                    "phone_number_id": (
                                        connection.phone_number_id
                                    ),
                                },
                                "statuses": [
                                    {
                                        "id": (
                                            "wamid.CAMPAIGN_STATUS_TEST"
                                        ),
                                        "status": (
                                            "delivered"
                                        ),
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

        body_bytes = json.dumps(
            payload,
            separators=(",", ":"),
        ).encode("utf-8")

        digest = hmac.new(
            secret.encode("utf-8"),
            body_bytes,
            hashlib.sha256,
        ).hexdigest()

        response = client.post(
            "/api/v1/meta/webhook",
            content=body_bytes,
            headers={
                "X-Hub-Signature-256": (
                    f"sha256={digest}"
                ),
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 200

        db_session.refresh(recipient)

        campaign = db_session.scalar(
            select(Campaign).where(
                Campaign.id == campaign_body["id"]
            )
        )

        db_session.refresh(campaign)

        assert recipient.status == "delivered"
        assert campaign.delivered_count == 1
    finally:
        clear_auth()
