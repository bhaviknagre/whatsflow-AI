from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CampaignRecipientInput(BaseModel):
    phone_number: str = Field(
        min_length=6,
        max_length=20,
    )
    contact_id: UUID | None = None
    parameters: list[str] = Field(
        default_factory=list
    )


class CreateCampaignRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=255,
    )
    template_name: str
    language_code: str
    recipients: list[CampaignRecipientInput] = Field(
        min_length=1,
    )
    scheduled_at: datetime | None = None


class CampaignRecipientResponse(BaseModel):
    id: UUID
    campaign_id: UUID
    contact_id: UUID | None
    phone_number: str
    parameters: list[str]
    rendered_text: str | None
    status: str
    whatsapp_message_id: str | None
    error_code: str | None
    error_message: str | None
    sent_at: datetime | None
    delivered_at: datetime | None
    read_at: datetime | None
    failed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class CampaignListItem(BaseModel):
    id: UUID
    organization_id: UUID
    whatsapp_connection_id: UUID
    name: str
    template_name: str
    language_code: str
    status: str
    scheduled_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    total_recipients: int
    sent_count: int
    delivered_count: int
    read_count: int
    failed_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class CampaignDetailResponse(CampaignListItem):
    recipients: list[CampaignRecipientResponse] = Field(
        default_factory=list
    )

    model_config = ConfigDict(
        from_attributes=True,
    )
