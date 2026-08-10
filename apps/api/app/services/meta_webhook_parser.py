from app.schemas.meta_webhook import (
    IncomingWhatsAppMessage,
    ParsedWhatsAppWebhook,
    WhatsAppMessageStatus,
)


def parse_whatsapp_webhook(
    payload: dict,
) -> ParsedWhatsAppWebhook:
    messages: list[IncomingWhatsAppMessage] = []
    statuses: list[WhatsAppMessageStatus] = []

    if payload.get("object") != "whatsapp_business_account":
        return ParsedWhatsAppWebhook(
            messages=[],
            statuses=[],
        )

    entries = payload.get("entry")

    if not isinstance(entries, list):
        return ParsedWhatsAppWebhook(
            messages=[],
            statuses=[],
        )

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        waba_id = entry.get("id")

        if not isinstance(waba_id, str) or not waba_id:
            continue

        changes = entry.get("changes")

        if not isinstance(changes, list):
            continue

        for change in changes:
            if not isinstance(change, dict):
                continue

            value = change.get("value")

            if not isinstance(value, dict):
                continue

            metadata = value.get("metadata")

            if not isinstance(metadata, dict):
                continue

            phone_number_id = metadata.get(
                "phone_number_id"
            )

            if (
                not isinstance(phone_number_id, str)
                or not phone_number_id
            ):
                continue

            profile_names_by_wa_id: dict[str, str] = {}

            raw_contacts = value.get("contacts", [])

            if isinstance(raw_contacts, list):
                for contact in raw_contacts:
                    if not isinstance(contact, dict):
                        continue

                    wa_id = contact.get("wa_id")
                    profile = contact.get("profile")

                    if not isinstance(wa_id, str):
                        continue

                    if not isinstance(profile, dict):
                        continue

                    profile_name = profile.get("name")

                    if isinstance(profile_name, str):
                        profile_names_by_wa_id[
                            wa_id
                        ] = profile_name

            raw_messages = value.get("messages", [])

            if isinstance(raw_messages, list):
                for message in raw_messages:
                    if not isinstance(message, dict):
                        continue

                    message_id = message.get("id")
                    from_phone_number = message.get(
                        "from"
                    )
                    timestamp = message.get(
                        "timestamp"
                    )
                    message_type = message.get(
                        "type"
                    )

                    if (
                        not message_id
                        or not from_phone_number
                        or not timestamp
                        or not message_type
                    ):
                        continue

                    text: str | None = None

                    if message_type == "text":
                        text_data = message.get(
                            "text",
                            {},
                        )

                        if isinstance(
                            text_data,
                            dict,
                        ):
                            text = text_data.get(
                                "body"
                            )

                    messages.append(
                        IncomingWhatsAppMessage(
                            message_id=message_id,
                            from_phone_number=(
                                from_phone_number
                            ),
                            timestamp=timestamp,
                            message_type=(
                                message_type
                            ),
                            text=text,
                            profile_name=(
                                profile_names_by_wa_id.get(
                                    from_phone_number
                                )
                            ),
                            phone_number_id=(
                                phone_number_id
                            ),
                            waba_id=waba_id,
                        )
                    )

            raw_statuses = value.get(
                "statuses",
                [],
            )

            if isinstance(raw_statuses, list):
                for status in raw_statuses:
                    if not isinstance(status, dict):
                        continue

                    message_id = status.get("id")
                    status_value = status.get(
                        "status"
                    )
                    timestamp = status.get(
                        "timestamp"
                    )

                    if (
                        not message_id
                        or not status_value
                        or not timestamp
                    ):
                        continue

                    statuses.append(
                        WhatsAppMessageStatus(
                            message_id=message_id,
                            status=status_value,
                            timestamp=timestamp,
                            recipient_id=(
                                status.get(
                                    "recipient_id"
                                )
                            ),
                        )
                    )

    return ParsedWhatsAppWebhook(
        messages=messages,
        statuses=statuses,
    )
