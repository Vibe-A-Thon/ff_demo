from app.core.logging_config import redact_payload


def test_redact_payload_masks_sensitive_fields():
    payload = {
        "password": "secret",
        "nested": {"api_key": "abc", "safe": "ok"},
        "items": [{"token": "t"}, {"value": 1}],
    }
    redacted = redact_payload(payload)
    assert redacted["password"] == "[REDACTED]"
    assert redacted["nested"]["api_key"] == "[REDACTED]"
    assert redacted["nested"]["safe"] == "ok"
    assert redacted["items"][0]["token"] == "[REDACTED]"
