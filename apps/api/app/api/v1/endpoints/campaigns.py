from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import (
    CurrentUser,
    get_current_user,
)
from app.core.encryption import token_encryption
from app.db.session import get_db
from app.models.campaign import Campaign
from app.models.contacts import Contact
from app.schemas.campaign import (
    CampaignDetailResponse,
    CampaignListItem,
    CreateCampaignRequest,
)
from app.services.campaigns import (
    cancel_campaign,
    create_campaign,
    recompute_campaign_counters,
    send_campaign,
)
from app.services.messages import (
    normalize_phone_number,
    render_template_body,
)
from app.services.meta_whatsapp import (
    MetaWhatsAppClient,
)
from app.services.whatsapp import get_connections

router = APIRouter(
    prefix="/campaigns",
    tags=["Campaigns"],
)


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


def _get_active_connection(
    db: Session,
    *,
    organization_id: UUID,
):
    connections = get_connections(
        db,
        organization_id,
    )

    if not connections:
        raise HTTPException(
            status_code=409,
            detail=(
                "No active WhatsApp connection"
                " configured"
            ),
        )

    return connections[0]


def _get_campaign(
    db: Session,
    *,
    organization_id: UUID,
    campaign_id: UUID,
) -> Campaign:
    campaign = db.scalar(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.organization_id
            == organization_id,
        )
    )

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail="Campaign not found",
        )

    return campaign


@router.post(
    "",
    response_model=CampaignDetailResponse,
)
async def create_campaign_endpoint(
    payload: CreateCampaignRequest,
    current_user: CurrentUser = Depends(
        get_current_user,
    ),
    db: Session = Depends(get_db),
):
    connection = _get_active_connection(
        db,
        organization_id=(
            current_user.organization_id
        ),
    )

    access_token = token_encryption.decrypt(
        connection.access_token_encrypted
    )

    client = MetaWhatsAppClient()

    try:
        templates = (
            await client.get_message_templates(
                waba_id=connection.waba_id,
                access_token=access_token,
            )
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=_describe_meta_error(exc),
        ) from exc

    template = next(
        (
            item
            for item in templates
            if item.name == payload.template_name
        ),
        None,
    )

    if template is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Template not found or not approved"
            ),
        )

    recipients_data = []

    for recipient in payload.recipients:
        phone_number = normalize_phone_number(
            recipient.phone_number,
        )

        contact = None

        if recipient.contact_id is not None:
            contact = db.scalar(
                select(Contact).where(
                    Contact.id == recipient.contact_id,
                    Contact.organization_id
                    == current_user.organization_id,
                )
            )

            if contact is None:
                raise HTTPException(
                    status_code=404,
                    detail=(
                        f"Contact not found: "
                        f"{recipient.contact_id}"
                    ),
                )

            if contact.is_blocked:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"Contact {phone_number} is blocked"
                    ),
                )

            # Always trust the CRM contact's phone number.
            phone_number = contact.phone_number

        if (
            len(recipient.parameters)
            != template.placeholder_count
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Expected "
                    f"{template.placeholder_count} "
                    "template parameter(s) for "
                    f"{phone_number}, got "
                    f"{len(recipient.parameters)}"
                ),
            )

        recipients_data.append(
            {
                "contact_id": (
                    contact.id
                    if contact is not None
                    else recipient.contact_id
                ),
                "phone_number": phone_number,
                "parameters": recipient.parameters,
                "rendered_text": (
                    render_template_body(
                        template.body_text,
                        recipient.parameters,
                    )
                ),
            }
        )

    campaign = create_campaign(
        db,
        organization_id=(
            current_user.organization_id
        ),
        whatsapp_connection_id=connection.id,
        name=payload.name,
        template_name=payload.template_name,
        language_code=payload.language_code,
        recipients=recipients_data,
        scheduled_at=payload.scheduled_at,
    )

    db.commit()
    db.refresh(campaign)

    return campaign


@router.get(
    "",
    response_model=list[CampaignListItem],
)
def list_campaigns(
    current_user: CurrentUser = Depends(
        get_current_user,
    ),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Campaign)
        .where(
            Campaign.organization_id
            == current_user.organization_id,
        )
        .order_by(Campaign.created_at.desc())
    ).all()


@router.get(
    "/{campaign_id}",
    response_model=CampaignDetailResponse,
)
def get_campaign(
    campaign_id: UUID,
    current_user: CurrentUser = Depends(
        get_current_user,
    ),
    db: Session = Depends(get_db),
):
    campaign = _get_campaign(
        db,
        organization_id=(
            current_user.organization_id
        ),
        campaign_id=campaign_id,
    )

    recompute_campaign_counters(db, campaign.id)
    db.refresh(campaign)

    return campaign


@router.post(
    "/{campaign_id}/send",
    response_model=CampaignDetailResponse,
)
async def send_campaign_endpoint(
    campaign_id: UUID,
    current_user: CurrentUser = Depends(
        get_current_user,
    ),
    db: Session = Depends(get_db),
):
    campaign = _get_campaign(
        db,
        organization_id=(
            current_user.organization_id
        ),
        campaign_id=campaign_id,
    )

    try:
        campaign = await send_campaign(
            db,
            campaign=campaign,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return campaign


@router.post(
    "/{campaign_id}/cancel",
    response_model=CampaignDetailResponse,
)
def cancel_campaign_endpoint(
    campaign_id: UUID,
    current_user: CurrentUser = Depends(
        get_current_user,
    ),
    db: Session = Depends(get_db),
):
    campaign = _get_campaign(
        db,
        organization_id=(
            current_user.organization_id
        ),
        campaign_id=campaign_id,
    )

    try:
        campaign = cancel_campaign(
            db,
            campaign=campaign,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return campaign
