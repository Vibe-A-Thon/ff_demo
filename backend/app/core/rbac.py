"""
Role-based access control mappings for Fraud Forge.
"""

from __future__ import annotations

from typing import Dict, Set


ROLE_SUPER_ADMIN = "super_admin"
ROLE_BANK_ADMIN = "bank_admin"
ROLE_FRAUD_OPERATOR = "bank_fraud_operator"
ROLE_FRAUD_ARCHITECT = "bank_fraud_architect"
ROLE_FRAUD_DEV = "bank_fraud_dev"
ROLE_TECH_LEAD = "bank_fraud_techlead"
ROLE_TECH_MANAGER = "bank_fraud_techmanager"
ROLE_AUDITOR = "bank_fraud_auditor"
ROLE_ANALYST = "analyst"

PERMISSIONS: Dict[str, Set[str]] = {
    ROLE_SUPER_ADMIN: {
        "battle:read",
        "battle:write",
        "evidence:read",
        "evidence:write",
        "rules:read",
        "rules:write",
        "rules:approve",
        "rules:deploy",
        "rsb:read",
        "rsb:write",
        "rsb:approve",
        "approvals:read",
        "approvals:write",
        "approvals:decide",
        "workflow:read",
        "workflow:control",
        "rag:read",
        "rag:write",
        "audit:read",
    },
    ROLE_BANK_ADMIN: {
        "battle:read",
        "battle:write",
        "evidence:read",
        "evidence:write",
        "rules:read",
        "rules:write",
        "rules:approve",
        "rules:deploy",
        "rsb:read",
        "rsb:write",
        "rsb:approve",
        "approvals:read",
        "approvals:write",
        "approvals:decide",
        "workflow:read",
        "workflow:control",
        "rag:read",
        "rag:write",
        "audit:read",
    },
    ROLE_FRAUD_OPERATOR: {
        "battle:read",
        "battle:write",
        "evidence:read",
        "evidence:write",
        "rules:read",
        "rsb:read",
        "approvals:read",
        "workflow:read",
        "workflow:control",
        "rag:read",
        "audit:read",
    },
    ROLE_FRAUD_ARCHITECT: {
        "battle:read",
        "evidence:read",
        "rules:read",
        "rules:write",
        "rules:approve",
        "rsb:read",
        "approvals:read",
        "workflow:read",
        "rag:read",
        "audit:read",
    },
    ROLE_FRAUD_DEV: {
        "battle:read",
        "evidence:read",
        "rules:read",
        "rules:write",
        "rsb:read",
        "rsb:write",
        "approvals:read",
        "workflow:read",
        "rag:read",
    },
    ROLE_TECH_LEAD: {
        "battle:read",
        "evidence:read",
        "rules:read",
        "rsb:read",
        "rsb:approve",
        "approvals:read",
        "approvals:decide",
        "workflow:read",
        "rag:read",
        "audit:read",
    },
    ROLE_TECH_MANAGER: {
        "battle:read",
        "evidence:read",
        "rules:read",
        "rules:deploy",
        "rsb:read",
        "rsb:approve",
        "approvals:read",
        "approvals:decide",
        "workflow:read",
        "workflow:control",
        "rag:read",
        "audit:read",
    },
    ROLE_AUDITOR: {
        "battle:read",
        "evidence:read",
        "rules:read",
        "rsb:read",
        "approvals:read",
        "workflow:read",
        "rag:read",
        "audit:read",
    },
    ROLE_ANALYST: {
        "battle:read",
        "evidence:read",
        "rules:read",
        "rsb:read",
        "approvals:read",
        "workflow:read",
        "rag:read",
    },
}


def has_permission(role: str, permission: str) -> bool:
    """Return True if the role has the requested permission.

    Args:
        role: Role identifier.
        permission: Permission string.

    Returns:
        True when permission is allowed.
    """
    return permission in PERMISSIONS.get(role, set())
