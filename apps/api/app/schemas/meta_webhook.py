from pydantic import BaseModel, ConfigDict


class WhatsAppMessageStatus(BaseModel):
    message_id: str
    status: str
    timestamp: str
    recipient_id: str | None = None

class IncomingWhatsAppMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message_id: str
    from_phone_number: str
    timestamp: str
    message_type: str
    text: str | None = None
    profile_name: str | None = None

    phone_number_id: str
    waba_id: str


class ParsedWhatsAppWebhook(BaseModel):
    messages: list[IncomingWhatsAppMessage] = []
    statuses: list[WhatsAppMessageStatus] = []
