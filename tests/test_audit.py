import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tenant_guard.audit import audit_inventory
from tenant_guard.reporting import remediation_plan, render_markdown

SAMPLE = Path(__file__).parents[1] / "inventory" / "sample-tenant.json"
NOW = datetime(2026, 8, 6, 12, 0, tzinfo=UTC)


def load_sample() -> dict:
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def test_sample_inventory_surfaces_cross_platform_findings() -> None:
    report = audit_inventory(load_sample(), now=NOW)
    rule_ids = {finding.rule_id for finding in report.findings}
    assert {
        "M365-IDENTITY-001",
        "M365-IDENTITY-002",
        "M365-IDENTITY-003",
        "M365-GUEST-001",
        "M365-APP-001",
        "M365-APP-002",
        "M365-CA-001",
        "AZURE-NETWORK-001",
        "AZURE-MONITOR-001",
        "AZURE-GOV-001",
    } <= rule_ids
    assert report.summary == {"critical": 1, "high": 4, "medium": 4, "low": 2}
    assert report.secure_score == 3


def test_findings_are_sorted_by_severity() -> None:
    report = audit_inventory(load_sample(), now=NOW)
    severities = [finding.severity for finding in report.findings]
    assert severities == sorted(
        severities, key={"critical": 0, "high": 1, "medium": 2, "low": 3}.get
    )


def test_remediation_plan_is_dry_run_and_requires_approval() -> None:
    report = audit_inventory(load_sample(), now=NOW)
    plan = remediation_plan(report)
    assert plan["mode"] == "dry-run"
    assert len(plan["actions"]) == len(report.findings)
    assert all(action["approval_required"] for action in plan["actions"])
    assert all(action["status"] == "proposed" for action in plan["actions"])


def test_markdown_explains_score_boundary() -> None:
    markdown = render_markdown(audit_inventory(load_sample(), now=NOW))
    assert "not Microsoft Secure Score" in markdown
    assert "dry-run only" in markdown
    assert "Privileged account has no registered MFA" in markdown


def test_missing_inventory_key_is_rejected() -> None:
    inventory = load_sample()
    del inventory["users"]
    with pytest.raises(ValueError, match="users"):
        audit_inventory(inventory, now=NOW)
