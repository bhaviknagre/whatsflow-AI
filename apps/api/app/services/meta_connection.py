from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.services.meta_whatsapp import (
    MetaWhatsAppClient,
)


@dataclass
class MetaValidatedConnection:
    access_token: str
    waba_id: str
    phone_number_id: str
    display_phone_number: str | None
    verified_name: str | None
    expires_at: datetime | None


class MetaConnectionService:
    def __init__(self) -> None:
        self.client = MetaWhatsAppClient()

    async def exchange_and_validate(
        self,
        *,
        code: str,
        waba_id: str,
        phone_number_id: str,
    ) -> MetaValidatedConnection:

        if not waba_id:
            raise ValueError(
                "Missing WhatsApp Business Account ID"
            )

        if not phone_number_id:
            raise ValueError(
                "Missing WhatsApp phone number ID"
            )

        token = await self.client.exchange_code(
            code
        )

        debug = await self.client.debug_token(
            token.access_token
        )

        data = debug.get("data", {})

        if not data.get("is_valid"):
            raise ValueError(
                "Meta access token is invalid"
            )

        if data.get("app_id") != self.client.app_id:
            raise ValueError(
                "Meta token belongs to another app"
            )

        long_lived_token = (
            await self.client.exchange_long_lived_token(
                token.access_token
            )
        )

        expires_at = (
            datetime.now(UTC)
            + timedelta(
                seconds=long_lived_token.expires_in
            )
            if long_lived_token.expires_in is not None
            else None
        )

        phones = (
            await self.client.get_waba_phone_numbers(
                waba_id,
                long_lived_token.access_token,
            )
        )

        phone = next(
            (
                item
                for item in phones
                if item.phone_number_id
                == phone_number_id
            ),
            None,
        )

        if phone is None:
            raise ValueError(
                "Phone number does not belong "
                "to the supplied WhatsApp "
                "Business Account"
            )

        return MetaValidatedConnection(
            access_token=long_lived_token.access_token,
            waba_id=waba_id,
            phone_number_id=phone.phone_number_id,
            display_phone_number=(
                phone.display_phone_number
            ),
            verified_name=phone.verified_name,
            expires_at=expires_at,
        )