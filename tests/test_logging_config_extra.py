import json
import logging
from io import StringIO

from app.core.logging_config import RedactingJsonFormatter, get_logger, coerce_log_payload
from app.core.request_context import set_correlation_id, set_request_id


def test_logger_formats_json_with_context():
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(RedactingJsonFormatter())

    logger = get_logger("test-logger")
    logger.logger.handlers = []
    logger.logger.addHandler(handler)
    logger.logger.setLevel(logging.INFO)

    set_correlation_id("cid-1")
    set_request_id("rid-1")

    logger.info("hello", extra={"payload": {"password": "secret", "value": 1}})
    payload = json.loads(stream.getvalue())
    assert payload["correlation_id"] == "cid-1"
    assert payload["request_id"] == "rid-1"
    assert payload["payload"]["password"] == "[REDACTED]"


def test_coerce_log_payload():
    extra = {"payload": {"a": 1}, "ignored": 2}
    assert coerce_log_payload(extra) == {"payload": {"a": 1}}
