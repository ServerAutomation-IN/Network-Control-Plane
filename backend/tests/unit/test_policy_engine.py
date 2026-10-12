"""Unit Tests for Policy Engine Service — Network Control Plane"""

import pytest
from app.services.policy import PolicyEngine
from app.schemas.policy import PolicySeverity, ComplianceStatus


def test_allowed_drivers_rule():
    """Verify allowed drivers policy evaluation."""
    engine = PolicyEngine(None)
    rules = {"allowed_drivers": ["bridge", "overlay"]}

    # Valid driver
    violations = engine.evaluate_rules(
        driver="bridge", labels={}, subnets=[], internal=False, rules_dict=rules
    )
    assert len(violations) == 0

    # Invalid driver
    violations = engine.evaluate_rules(
        driver="macvlan", labels={}, subnets=[], internal=False, rules_dict=rules
    )
    assert len(violations) == 1
    assert violations[0].rule_type == "driver"
    assert "macvlan" in violations[0].message


def test_blocked_drivers_rule():
    """Verify blocked drivers policy evaluation."""
    engine = PolicyEngine(None)
    rules = {"blocked_drivers": ["host", "null"]}

    violations = engine.evaluate_rules(
        driver="host", labels={}, subnets=[], internal=False, rules_dict=rules
    )
    assert len(violations) == 1
    assert violations[0].rule_type == "driver"
    assert "forbidden" in violations[0].message


def test_required_labels_rule():
    """Verify required labels policy evaluation."""
    engine = PolicyEngine(None)
    rules = {
        "required_labels": {"environment": "production", "owner": "platform"},
        "required_label_keys": ["managed-by"],
    }

    # Complete labels
    violations = engine.evaluate_rules(
        driver="bridge",
        labels={"environment": "production", "owner": "platform", "managed-by": "control-plane"},
        subnets=[],
        internal=False,
        rules_dict=rules,
    )
    assert len(violations) == 0

    # Missing label key and value mismatch
    violations = engine.evaluate_rules(
        driver="bridge",
        labels={"environment": "staging"},
        subnets=[],
        internal=False,
        rules_dict=rules,
    )
    assert len(violations) == 3  # env mismatch, missing owner, missing managed-by key


def test_approved_cidr_ranges_rule():
    """Verify CIDR range boundary policy evaluation."""
    engine = PolicyEngine(None)
    rules = {"approved_cidr_ranges": ["172.16.0.0/12", "10.0.0.0/8"]}

    # Compliant subnet
    violations = engine.evaluate_rules(
        driver="bridge", labels={}, subnets=["172.19.0.0/16"], internal=False, rules_dict=rules
    )
    assert len(violations) == 0

    # Non-compliant subnet (e.g. 192.168.1.0/24 outside approved 172.16/12 and 10/8)
    violations = engine.evaluate_rules(
        driver="bridge", labels={}, subnets=["192.168.1.0/24"], internal=False, rules_dict=rules
    )
    assert len(violations) == 1
    assert violations[0].rule_type == "cidr"
    assert "outside approved CIDR" in violations[0].message


def test_require_internal_and_max_subnets_rule():
    """Verify internal requirement and max subnets capacity rules."""
    engine = PolicyEngine(None)
    rules = {"require_internal": True, "max_subnets_per_network": 1}

    violations = engine.evaluate_rules(
        driver="bridge",
        labels={},
        subnets=["172.19.0.0/16", "172.20.0.0/16"],
        internal=False,
        rules_dict=rules,
    )
    assert len(violations) == 2
    rule_types = [v.rule_type for v in violations]
    assert "internal" in rule_types
    assert "capacity" in rule_types
