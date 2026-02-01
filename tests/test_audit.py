from app.audit import redact_evidence_pack, compute_checksum, rule_tests_pass


def test_redact_evidence_pack_external():
    pack = {
        "logs": [{"event_type": "x", "rule_id": "R1", "secret": "x"}],
        "contributing_factors": [{"factor": "A", "weight": 0.5}],
        "keep": "ok",
    }
    redacted = redact_evidence_pack(pack, mode="external")
    assert redacted["logs"][0] == {"event_type": "x", "rule_id": "R1"}
    assert redacted["contributing_factors"][0] == {"factor": "A"}


def test_compute_checksum_stable():
    payload = {"a": 1, "b": 2}
    assert compute_checksum(payload) == compute_checksum(payload)


def test_rule_tests_pass():
    assert rule_tests_pass({"failed": 0, "coverage": 80}) is True
    assert rule_tests_pass({"failed": 1, "coverage": 90}) is False
