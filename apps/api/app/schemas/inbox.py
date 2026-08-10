from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WhatsAppConnectionSummary(BaseModel):
    id: UUID
    waba_id: str
    phone_number_id: str
    display_phone_number: str | None
    verified_name: str | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class SendMessageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4096)


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    whatsapp_message_id: str | None
    direction: str
    message_type: str
    text: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    id: UUID
    whatsapp_connection_id: UUID
    customer_phone_number: str
    unread_count: int
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse]
    whatsapp_connection: WhatsAppConnectionSummary

    model_config = ConfigDict(from_attributes=True)


class ConversationListItem(BaseModel):
    id: UUID
    whatsapp_connection_id: UUID
    customer_phone_number: str
    last_message: MessageResponse | None
    unread_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageTemplateSummary(BaseModel):
    name: str
    language: str
    category: str
    body_text: str | None
    placeholder_count: int


class StartConversationRequest(BaseModel):
    customer_phone_number: str
    template_name: str
    language_code: str
    parameters: list[str] = Field(default_factory=list)
