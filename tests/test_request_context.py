from app.core.request_context import (
    set_correlation_id,
    set_request_id,
    get_correlation_id,
    get_request_id,
)


def test_request_context_set_and_get():
    set_correlation_id("cid")
    set_request_id("rid")
    assert get_correlation_id() == "cid"
    assert get_request_id() == "rid"
