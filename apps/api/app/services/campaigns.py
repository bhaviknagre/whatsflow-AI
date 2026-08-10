from datetime import UTC, datetime
from uuid import UUID

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.campaign import Campaign, CampaignRecipient
from app.models.message import Message
from app.models.whatsapp_connection import (
    WhatsAppConnection,
)
from app.services.messages import send_template_message

RECIPIENT_STATUS_ORDER = {
    "pending": 0,
    "sending": 1,
    "sent": 2,
    "delivered": 3,
    "read": 4,
}


def _describe_meta_error(exc: httpx.HTTPStatusError) -> str:
    try:
        message = exc.response.json().get(
            "error", {}
        ).get("message")
    except ValueError:
        message = None

    if message:
        return f"WhatsApp API error: {message}"

    return (
        "WhatsApp API error: "
        f"{exc.response.status_code}"
    )


def create_campaign(
    db: Session,
    *,
    organization_id: UUID,
    whatsapp_connection_id: UUID,
    name: str,
    template_name: str,
    language_code: str,
    recipients: list[dict],
    scheduled_at: datetime | None,
) -> Campaign:
    campaign = Campaign(
        organization_id=organization_id,
        whatsapp_connection_id=(
            whatsapp_connection_id
        ),
        name=name,
        template_name=template_name,
        language_code=language_code,
        status=(
            "scheduled"
            if scheduled_at is not None
            else "draft"
        ),
        scheduled_at=scheduled_at,
        total_recipients=len(recipients),
    )

    db.add(campaign)
    db.flush()

    for recipient in recipients:
        db.add(
            CampaignRecipient(
                campaign_id=campaign.id,
                contact_id=recipient.get(
                    "contact_id"
                ),
                phone_number=recipient[
                    "phone_number"
                ],
                parameters=recipient[
                    "parameters"
                ],
                rendered_text=recipient[
                    "rendered_text"
                ],
                status="pending",
            )
        )

    db.flush()

    return campaign


async def send_campaign(
    db: Session,
    *,
    campaign: Campaign,
) -> Campaign:
    if campaign.status not in {
        "draft",
        "scheduled",
    }:
        raise ValueError(
            "Campaign has already been sent"
        )

    campaign.status = "running"
    campaign.started_at = datetime.now(UTC)

    db.commit()

    connection = db.get(
        WhatsAppConnection,
        campaign.whatsapp_connection_id,
    )

    if (
        connection is None
        or not connection.is_active
    ):
        campaign.status = "failed"
        db.commit()

        raise ValueError(
            "WhatsApp connection is not active"
        )

    recipients = db.scalars(
        select(CampaignRecipient).where(
            CampaignRecipient.campaign_id
            == campaign.id,
            CampaignRecipient.status == "pending",
        )
    ).all()

    try:
        for recipient in recipients:
            recipient.status = "sending"
            db.flush()

            try:
                message = (
                    await send_template_message(
                        db,
                        organization_id=(
                            campaign.organization_id
                        ),
                        whatsapp_connection=(
                            connection
                        ),
                        customer_phone_number=(
                            recipient.phone_number
                        ),
                        template_name=(
                            campaign.template_name
                        ),
                        language_code=(
                            campaign.language_code
                        ),
                        parameters=(
                            recipient.parameters
                        ),
                        rendered_text=(
                            recipient.rendered_text
                            or ""
                        ),
                    )
                )

                recipient.whatsapp_message_id = (
                    message.whatsapp_message_id
                )
                recipient.status = "sent"
                recipient.sent_at = datetime.now(
                    UTC
                )

                campaign.sent_count += 1

                db.commit()

            except httpx.HTTPStatusError as exc:
                db.rollback()

                recipient.status = "failed"
                recipient.error_message = (
                    _describe_meta_error(exc)
                )
                recipient.failed_at = datetime.now(
                    UTC
                )

                campaign.failed_count += 1

                db.commit()

            except ValueError as exc:
                db.rollback()

                recipient.status = "failed"
                recipient.error_message = str(exc)
                recipient.failed_at = datetime.now(
                    UTC
                )

                campaign.failed_count += 1

                db.commit()

        campaign.status = "completed"
        campaign.completed_at = datetime.now(UTC)

        db.commit()

    except Exception:
        db.rollback()

        campaign.status = "failed"

        db.commit()

        raise

    db.refresh(campaign)

    return campaign


def cancel_campaign(
    db: Session,
    *,
    campaign: Campaign,
) -> Campaign:
    if campaign.status not in {
        "draft",
        "scheduled",
    }:
        raise ValueError(
            "Only draft or scheduled campaigns"
            " can be cancelled"
        )

    campaign.status = "cancelled"

    db.commit()
    db.refresh(campaign)

    return campaign


def sync_campaign_recipient_status(
    db: Session,
    *,
    message: Message,
) -> None:
    if message.status not in {
        "sent",
        "delivered",
        "read",
        "failed",
    }:
        return

    recipient = db.scalar(
        select(CampaignRecipient).where(
            CampaignRecipient.whatsapp_message_id
            == message.whatsapp_message_id
        )
    )

    if recipient is None:
        return

    previous_status = recipient.status

    current_rank = RECIPIENT_STATUS_ORDER.get(
        recipient.status,
        0,
    )

    new_rank = RECIPIENT_STATUS_ORDER.get(
        message.status,
        current_rank,
    )

    if (
        message.status == "failed"
        or new_rank >= current_rank
    ):
        recipient.status = message.status

    if recipient.status == previous_status:
        return

    now = datetime.now(UTC)
    campaign = db.get(
        Campaign,
        recipient.campaign_id,
    )

    if recipient.status == "delivered":
        recipient.delivered_at = now

        if campaign is not None:
            campaign.delivered_count += 1

    elif recipient.status == "read":
        recipient.read_at = now

        if campaign is not None:
            campaign.read_count += 1

    elif recipient.status == "failed":
        recipient.failed_at = now

        if campaign is not None:
            campaign.failed_count += 1


def recompute_campaign_counters(
    db: Session,
    campaign_id: UUID,
) -> Campaign | None:
    campaign = db.get(Campaign, campaign_id)

    if campaign is None:
        return None

    total = db.scalar(
        select(func.count()).where(
            CampaignRecipient.campaign_id
            == campaign_id
        )
    ) or 0

    sent = db.scalar(
        select(func.count()).where(
            CampaignRecipient.campaign_id
            == campaign_id,
            CampaignRecipient.status.in_(
                ["sent", "delivered", "read"]
            ),
        )
    ) or 0

    delivered = db.scalar(
        select(func.count()).where(
            CampaignRecipient.campaign_id
            == campaign_id,
            CampaignRecipient.status.in_(
                ["delivered", "read"]
            ),
        )
    ) or 0

    read = db.scalar(
        select(func.count()).where(
            CampaignRecipient.campaign_id
            == campaign_id,
            CampaignRecipient.status == "read",
        )
    ) or 0

    failed = db.scalar(
        select(func.count()).where(
            CampaignRecipient.campaign_id
            == campaign_id,
            CampaignRecipient.status == "failed",
        )
    ) or 0

    campaign.total_recipients = total
    campaign.sent_count = sent
    campaign.delivered_count = delivered
    campaign.read_count = read
    campaign.failed_count = failed

    db.commit()
    db.refresh(campaign)

    return campaign
