from app.core.rbac import has_permission


def test_has_permission_allows_known_role():
    assert has_permission("bank_admin", "rules:read") is True


def test_has_permission_denies_unknown_role():
    assert has_permission("unknown", "rules:read") is False
