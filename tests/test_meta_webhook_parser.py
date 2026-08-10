from app.services.meta_webhook_parser import (
    parse_whatsapp_webhook,
)


def test_parse_text_message():
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": (
                                    "15550001111"
                                ),
                                "phone_number_id": (
                                    "111222333"
                                ),
                            },
                            "messages": [
                                {
                                    "from": (
                                        "919876543210"
                                    ),
                                    "id": (
                                        "wamid.TEST123"
                                    ),
                                    "timestamp": (
                                        "1750000000"
                                    ),
                                    "type": "text",
                                    "text": {
                                        "body": (
                                            "Hello WhatsFlow"
                                        )
                                    },
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }

    result = parse_whatsapp_webhook(
        payload
    )

    assert len(result.messages) == 1

    message = result.messages[0]

    assert message.message_id == "wamid.TEST123"
    assert (
        message.from_phone_number
        == "919876543210"
    )
    assert message.message_type == "text"
    assert message.text == "Hello WhatsFlow"
    assert message.phone_number_id == "111222333"
    assert message.waba_id == "123456789"


def test_ignore_non_whatsapp_payload():
    payload = {
        "object": "something_else",
    }

    result = parse_whatsapp_webhook(
        payload
    )

    assert result.messages == []


def test_ignore_message_without_required_fields():
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "value": {
                            "metadata": {
                                "phone_number_id": (
                                    "111222333"
                                ),
                            },
                            "messages": [
                                {
                                    "type": "text",
                                    "text": {
                                        "body": "Hello"
                                    },
                                }
                            ],
                        }
                    }
                ],
            }
        ],
    }

    result = parse_whatsapp_webhook(
        payload
    )

    assert result.messages == []

def test_parse_text_whatsapp_message():
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WABA_123",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "metadata": {
                                "phone_number_id": "PHONE_123",
                            },
                            "messages": [
                                {
                                    "id": "wamid.TEST_123",
                                    "from": "919876543210",
                                    "timestamp": "1750000000",
                                    "type": "text",
                                    "text": {
                                        "body": "Hello WhatsFlow"
                                    },
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }

    result = parse_whatsapp_webhook(payload)

    assert len(result.messages) == 1

    message = result.messages[0]

    assert message.message_id == "wamid.TEST_123"
    assert message.from_phone_number == "919876543210"
    assert message.phone_number_id == "PHONE_123"
    assert message.waba_id == "WABA_123"
    assert message.message_type == "text"
    assert message.text == "Hello WhatsFlow"


def test_parse_whatsapp_webhook_status():
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "TEST_WABA_ID",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "metadata": {
                                "phone_number_id": (
                                    "TEST_PHONE_ID"
                                ),
                            },
                            "statuses": [
                                {
                                    "id": (
                                        "wamid.STATUS_001"
                                    ),
                                    "status": "delivered",
                                    "timestamp": (
                                        "1750000000"
                                    ),
                                    "recipient_id": (
                                        "919999999999"
                                    ),
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }

    parsed = parse_whatsapp_webhook(
        payload
    )

    assert len(parsed.statuses) == 1

    status = parsed.statuses[0]

    assert status.message_id == (
        "wamid.STATUS_001"
    )
    assert status.status == "delivered"
    assert status.timestamp == "1750000000"
    assert status.recipient_id == (
        "919999999999"
    )


def test_null_entry_does_not_crash():
    payload = {
        "object": "whatsapp_business_account",
        "entry": None,
    }

    result = parse_whatsapp_webhook(payload)

    assert result.messages == []
    assert result.statuses == []


def test_empty_entry_object_does_not_crash():
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{}],
    }

    result = parse_whatsapp_webhook(payload)

    assert result.messages == []
    assert result.statuses == []


def test_null_changes_does_not_crash():
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": None,
            }
        ],
    }

    result = parse_whatsapp_webhook(payload)

    assert result.messages == []
    assert result.statuses == []


def test_null_value_does_not_crash():
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "field": "messages",
                        "value": None,
                    }
                ],
            }
        ],
    }

    result = parse_whatsapp_webhook(payload)

    assert result.messages == []
    assert result.statuses == []


def test_non_dict_entries_are_skipped():
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            "not a dict",
            123,
            None,
            {
                "id": "123456789",
                "changes": [
                    "not a dict",
                    None,
                    {
                        "field": "messages",
                        "value": {
                            "metadata": {
                                "phone_number_id": (
                                    "111222333"
                                ),
                            },
                            "messages": [
                                "not a dict",
                                None,
                                {
                                    "id": (
                                        "wamid.MIXED_001"
                                    ),
                                    "from": (
                                        "919876543210"
                                    ),
                                    "timestamp": (
                                        "1750000000"
                                    ),
                                    "type": "text",
                                    "text": {
                                        "body": "Hi"
                                    },
                                },
                            ],
                        },
                    },
                ],
            },
        ],
    }

    result = parse_whatsapp_webhook(payload)

    assert len(result.messages) == 1
    assert (
        result.messages[0].message_id
        == "wamid.MIXED_001"
    )