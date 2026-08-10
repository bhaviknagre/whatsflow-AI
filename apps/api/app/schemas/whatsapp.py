from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WhatsAppConnectionResponse(BaseModel):
    id: UUID
    waba_id: str
    phone_number_id: str
    display_phone_number: str | None
    verified_name: str | None
    is_active: bool
    expires_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True
    )


class MetaConnectResponse(BaseModel):
    state: str


class MetaCallbackResponse(BaseModel):
    connection_id: UUID
    waba_id: str
    phone_number_id: str
    display_phone_number: str | None
    verified_name: str | None

    model_config = ConfigDict(
        from_attributes=True
    )


class MetaSignupRequest(BaseModel):
    code: str
    state: str
    waba_id: str
    phone_number_id: str
    session_info: dict | None = None


class MetaSignupResponse(BaseModel):
    status: str
    connection_id: UUID | None = None


class SendWhatsAppMessageRequest(BaseModel):
    text: str


class SendWhatsAppMessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    whatsapp_message_id: str
    direction: str
    message_type: str
    text: str | None
    status: str