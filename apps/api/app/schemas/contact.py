from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ContactCreateRequest(BaseModel):
    phone_number: str = Field(min_length=5, max_length=50)
    name: str | None = Field(default=None, max_length=255)


class ContactUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    is_blocked: bool | None = None


class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    phone_number: str
    name: str | None
    profile_name: str | None
    is_blocked: bool
    created_at: datetime
    updated_at: datetime
