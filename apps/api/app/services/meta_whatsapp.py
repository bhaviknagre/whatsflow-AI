import re
from dataclasses import dataclass

import httpx

from app.core.config import settings

_PLACEHOLDER_PATTERN = re.compile(r"\{\{\d+\}\}")


@dataclass
class WhatsAppPhoneNumber:
    phone_number_id: str
    display_phone_number: str | None
    verified_name: str | None


@dataclass
class MetaAccessToken:
    access_token: str
    token_type: str
    expires_in: int | None

@dataclass
class WhatsAppSendResult:
    message_id: str


@dataclass
class WhatsAppMessageTemplate:
    name: str
    language: str
    category: str
    status: str
    body_text: str | None
    placeholder_count: int


class MetaWhatsAppClient:
    def __init__(self) -> None:
        self.app_id = settings.META_APP_ID

        self.base_url = (
            f"https://graph.facebook.com/"
            f"{settings.META_GRAPH_API_VERSION}"
        )

    async def exchange_code(
        self,
        code: str,
    ) -> MetaAccessToken:
        url = f"{self.base_url}/oauth/access_token"

        params = {
            "client_id": settings.META_APP_ID,
            "client_secret": settings.META_APP_SECRET,
            "code": code,
        }

        async with httpx.AsyncClient(
            timeout=15.0,
        ) as client:
            response = await client.get(
                url,
                params=params,
            )

        response.raise_for_status()

        data = response.json()

        return MetaAccessToken(
            access_token=data["access_token"],
            token_type=data.get(
                "token_type",
                "bearer",
            ),
            expires_in=data.get("expires_in"),
        )

    async def exchange_long_lived_token(
        self,
        short_lived_token: str,
    ) -> MetaAccessToken:
        url = f"{self.base_url}/oauth/access_token"

        params = {
            "grant_type": "fb_exchange_token",
            "client_id": settings.META_APP_ID,
            "client_secret": settings.META_APP_SECRET,
            "fb_exchange_token": short_lived_token,
        }

        async with httpx.AsyncClient(
            timeout=15.0,
        ) as client:
            response = await client.get(
                url,
                params=params,
            )

        response.raise_for_status()

        data = response.json()

        return MetaAccessToken(
            access_token=data["access_token"],
            token_type=data.get(
                "token_type",
                "bearer",
            ),
            expires_in=data.get("expires_in"),
        )

    async def debug_token(
        self,
        access_token: str,
    ) -> dict:
        url = f"{self.base_url}/debug_token"

        params = {
            "input_token": access_token,
            "access_token": (
                f"{settings.META_APP_ID}|"
                f"{settings.META_APP_SECRET}"
            ),
        }

        async with httpx.AsyncClient(
            timeout=15.0,
        ) as client:
            response = await client.get(
                url,
                params=params,
            )

        response.raise_for_status()

        return response.json()

    async def get_phone_number(
        self,
        phone_number_id: str,
        access_token: str,
    ) -> WhatsAppPhoneNumber:
        url = f"{self.base_url}/{phone_number_id}"

        params = {
            "fields": (
                "id,"
                "display_phone_number,"
                "verified_name"
            ),
        }

        headers = {
            "Authorization": (
                f"Bearer {access_token}"
            ),
        }

        async with httpx.AsyncClient(
            timeout=15.0,
        ) as client:
            response = await client.get(
                url,
                params=params,
                headers=headers,
            )

        response.raise_for_status()

        data = response.json()

        return WhatsAppPhoneNumber(
            phone_number_id=data["id"],
            display_phone_number=data.get(
                "display_phone_number"
            ),
            verified_name=data.get(
                "verified_name"
            ),
        )

    async def get_waba_phone_numbers(
        self,
        waba_id: str,
        access_token: str,
    ) -> list[WhatsAppPhoneNumber]:
        url = (
            f"{self.base_url}/"
            f"{waba_id}/phone_numbers"
        )

        headers = {
            "Authorization": (
                f"Bearer {access_token}"
            ),
        }

        async with httpx.AsyncClient(
            timeout=15.0,
        ) as client:
            response = await client.get(
                url,
                headers=headers,
            )

        response.raise_for_status()

        data = response.json()

        return [
            WhatsAppPhoneNumber(
                phone_number_id=item["id"],
                display_phone_number=item.get(
                    "display_phone_number"
                ),
                verified_name=item.get(
                    "verified_name"
                ),
            )
            for item in data.get("data", [])
        ]

    async def send_text_message(
        self,
        *,
        phone_number_id: str,
        access_token: str,
        recipient_phone_number: str,
        text: str,
    ) -> WhatsAppSendResult:
        url = (
            f"{self.base_url}/"
            f"{phone_number_id}/messages"
        )

        headers = {
            "Authorization": (
                f"Bearer {access_token}"
            ),
            "Content-Type": "application/json",
        }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": text,
            },
        }

        async with httpx.AsyncClient(
            timeout=15.0,
        ) as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload,
            )

        response.raise_for_status()

        return self._extract_send_result(
            response.json()
        )

    async def get_message_templates(
        self,
        *,
        waba_id: str,
        access_token: str,
    ) -> list[WhatsAppMessageTemplate]:
        url = (
            f"{self.base_url}/"
            f"{waba_id}/message_templates"
        )

        params = {
            "fields": (
                "name,status,language,"
                "category,components"
            ),
        }

        headers = {
            "Authorization": (
                f"Bearer {access_token}"
            ),
        }

        async with httpx.AsyncClient(
            timeout=15.0,
        ) as client:
            response = await client.get(
                url,
                params=params,
                headers=headers,
            )

        response.raise_for_status()

        data = response.json()

        templates = []

        for item in data.get("data", []):
            if item.get("status") != "APPROVED":
                continue

            # Only BODY variables are supported; HEADER/BUTTONS
            # components with their own variables are ignored.
            body_text = None

            for component in item.get(
                "components", []
            ):
                if (
                    component.get("type", "").upper()
                    == "BODY"
                ):
                    body_text = component.get("text")
                    break

            placeholder_count = (
                len(
                    _PLACEHOLDER_PATTERN.findall(
                        body_text
                    )
                )
                if body_text
                else 0
            )

            templates.append(
                WhatsAppMessageTemplate(
                    name=item["name"],
                    language=item["language"],
                    category=item.get(
                        "category", ""
                    ),
                    status=item["status"],
                    body_text=body_text,
                    placeholder_count=(
                        placeholder_count
                    ),
                )
            )

        return templates

    async def send_template_message(
        self,
        *,
        phone_number_id: str,
        access_token: str,
        recipient_phone_number: str,
        template_name: str,
        language_code: str,
        parameters: list[str],
    ) -> WhatsAppSendResult:
        url = (
            f"{self.base_url}/"
            f"{phone_number_id}/messages"
        )

        headers = {
            "Authorization": (
                f"Bearer {access_token}"
            ),
            "Content-Type": "application/json",
        }

        components = (
            [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": value,
                        }
                        for value in parameters
                    ],
                }
            ]
            if parameters
            else []
        )

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code,
                },
                "components": components,
            },
        }

        async with httpx.AsyncClient(
            timeout=15.0,
        ) as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload,
            )

        response.raise_for_status()

        return self._extract_send_result(
            response.json()
        )

    def _extract_send_result(
        self,
        data: dict,
    ) -> WhatsAppSendResult:
        messages = data.get("messages", [])

        if not messages:
            raise ValueError(
                "Meta did not return a message ID"
            )

        message_id = messages[0].get("id")

        if not message_id:
            raise ValueError(
                "Meta response did not contain a message ID"
            )

        return WhatsAppSendResult(
            message_id=message_id,
        )