


def test_whatsapp_message_payload_is_processed():
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
                                "phone_number_id": "TEST_PHONE_ID",
                            },
                            "messages": [
                                {
                                    "id": "wamid.TEST_MESSAGE_001",
                                    "from": "919999999999",
                                    "timestamp": "1750000000",
                                    "type": "text",
                                    "text": {
                                        "body": "Hello WhatsFlow!"
                                    },
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }

    assert payload["object"] == (
        "whatsapp_business_account"
    )

    messages = (
        payload["entry"][0]["changes"][0]
        ["value"]["messages"]
    )

    assert len(messages) == 1
    assert messages[0]["id"] == (
        "wamid.TEST_MESSAGE_001"
    )
    assert messages[0]["text"]["body"] == (
        "Hello WhatsFlow!"
    )