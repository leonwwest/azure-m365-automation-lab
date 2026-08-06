"""Deterministic governance checks for sanitized Azure and M365 inventories."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

SEVERITY_WEIGHT = {"critical": 25, "high": 12, "medium": 5, "low": 2}
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    resource: str
    title: str
    evidence: str
    recommendation: str


@dataclass(frozen=True)
class AuditReport:
    tenant: str
    generated_at: str
    inventory_generated_at: str
    findings: tuple[Finding, ...]
    secure_score: int
    summary: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant": self.tenant,
            "generated_at": self.generated_at,
            "inventory_generated_at": self.inventory_generated_at,
            "secure_score": self.secure_score,
            "summary": self.summary,
            "findings": [asdict(finding) for finding in self.findings],
        }


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _days_since(value: str, now: datetime) -> int:
    return max(0, (now - _parse_timestamp(value)).days)


def _finding(
    rule_id: str,
    severity: str,
    resource: str,
    title: str,
    evidence: str,
    recommendation: str,
) -> Finding:
    return Finding(rule_id, severity, resource, title, evidence, recommendation)


def _audit_users(users: Iterable[dict[str, Any]], now: datetime) -> list[Finding]:
    findings: list[Finding] = []
    enabled_break_glass = 0
    for user in users:
        name = user["display_name"]
        resource = f"user:{name}"
        if user.get("break_glass") and user.get("enabled", True):
            enabled_break_glass += 1
        if not user.get("enabled", True):
            continue
        if user.get("is_privileged") and not user.get("mfa_registered"):
            findings.append(
                _finding(
                    "M365-IDENTITY-001",
                    "critical",
                    resource,
                    "Privileged account has no registered MFA method",
                    "The sanitized inventory marks the account as privileged and MFA=false.",
                    "Register phishing-resistant MFA and verify Conditional Access coverage.",
                )
            )
        last_sign_in = user.get("last_sign_in_at")
        if user.get("is_privileged") and last_sign_in:
            age = _days_since(last_sign_in, now)
            if age > 30:
                findings.append(
                    _finding(
                        "M365-IDENTITY-002",
                        "high",
                        resource,
                        "Privileged account is inactive",
                        f"Last sign-in was {age} days ago; the threshold is 30 days.",
                        "Review the role assignment and disable or remove standing privilege.",
                    )
                )
        if user.get("user_type") == "Guest" and last_sign_in:
            age = _days_since(last_sign_in, now)
            if age > 90:
                findings.append(
                    _finding(
                        "M365-GUEST-001",
                        "medium",
                        resource,
                        "Guest account is stale",
                        f"Last sign-in was {age} days ago; the guest threshold is 90 days.",
                        "Ask the sponsor to recertify access or remove the guest account.",
                    )
                )
        if user.get("user_type", "Member") == "Member" and not user.get("licenses", []):
            findings.append(
                _finding(
                    "M365-LICENSE-001",
                    "low",
                    resource,
                    "Enabled member has no assigned license",
                    "The account is enabled but the license list is empty.",
                    "Confirm whether the identity is service-only or assign the approved license.",
                )
            )
    if enabled_break_glass < 2:
        findings.append(
            _finding(
                "M365-IDENTITY-003",
                "medium",
                "tenant:identity",
                "Fewer than two emergency access accounts",
                f"Inventory contains {enabled_break_glass} enabled break-glass account(s).",
                "Maintain two monitored cloud-only emergency accounts with tested procedures.",
            )
        )
    return findings


def _audit_service_principals(
    principals: Iterable[dict[str, Any]], now: datetime
) -> list[Finding]:
    findings: list[Finding] = []
    for principal in principals:
        name = principal["display_name"]
        resource = f"service-principal:{name}"
        owners = principal.get("owners", [])
        if not owners:
            findings.append(
                _finding(
                    "M365-APP-001",
                    "medium",
                    resource,
                    "Enterprise application has no accountable owner",
                    "The owners collection is empty.",
                    "Assign at least two accountable owners and record the business purpose.",
                )
            )
        expiry = principal.get("credential_expires_at")
        if expiry:
            days_left = (_parse_timestamp(expiry) - now).days
            if days_left < 0:
                severity = "critical"
                title = "Application credential is expired"
            elif days_left <= 30:
                severity = "high"
                title = "Application credential expires within 30 days"
            else:
                continue
            findings.append(
                _finding(
                    "M365-APP-002",
                    severity,
                    resource,
                    title,
                    f"Credential lifetime remaining: {days_left} days.",
                    "Rotate the credential, prefer workload identity, and verify dependent jobs.",
                )
            )
    return findings


def _audit_conditional_access(policies: Iterable[dict[str, Any]]) -> list[Finding]:
    enabled = [policy for policy in policies if policy.get("state") == "enabled"]
    mfa_policies = [policy for policy in enabled if "mfa" in policy.get("grant_controls", [])]
    if mfa_policies:
        return []
    return [
        _finding(
            "M365-CA-001",
            "high",
            "tenant:conditional-access",
            "No enabled Conditional Access policy requires MFA",
            "No enabled policy contains the mfa grant control.",
            "Deploy a report-only baseline, validate exclusions, then enable MFA enforcement.",
        )
    ]


def _audit_azure_resources(resources: Iterable[dict[str, Any]]) -> list[Finding]:
    findings: list[Finding] = []
    for resource_data in resources:
        resource = f"azure:{resource_data['type']}:{resource_data['name']}"
        if resource_data.get("public_network_access") == "Enabled":
            findings.append(
                _finding(
                    "AZURE-NETWORK-001",
                    "high",
                    resource,
                    "Public network access is enabled",
                    "The inventory exposes this resource through a public endpoint.",
                    "Validate the use case and prefer a private endpoint with restricted DNS.",
                )
            )
        if not resource_data.get("diagnostic_settings"):
            findings.append(
                _finding(
                    "AZURE-MONITOR-001",
                    "medium",
                    resource,
                    "Diagnostic settings are missing",
                    "No diagnostic destination is recorded for this resource.",
                    "Route platform logs and metrics to the approved Log Analytics workspace.",
                )
            )
        tags = resource_data.get("tags", {})
        missing_tags = [tag for tag in ("owner", "cost_center", "environment") if not tags.get(tag)]
        if missing_tags:
            findings.append(
                _finding(
                    "AZURE-GOV-001",
                    "low",
                    resource,
                    "Required governance tags are incomplete",
                    f"Missing tags: {', '.join(missing_tags)}.",
                    "Apply the approved owner, cost_center and environment tags.",
                )
            )
    return findings


def audit_inventory(inventory: dict[str, Any], now: datetime | None = None) -> AuditReport:
    """Audit one sanitized inventory and return a stable, serializable report."""
    now = (now or datetime.now(UTC)).astimezone(UTC)
    required = {"tenant", "generated_at", "users", "service_principals"}
    missing = required.difference(inventory)
    if missing:
        raise ValueError(f"inventory is missing required keys: {', '.join(sorted(missing))}")

    findings = [
        *_audit_users(inventory["users"], now),
        *_audit_service_principals(inventory["service_principals"], now),
        *_audit_conditional_access(inventory.get("conditional_access_policies", [])),
        *_audit_azure_resources(inventory.get("azure_resources", [])),
    ]
    findings.sort(key=lambda item: (SEVERITY_ORDER[item.severity], item.rule_id, item.resource))
    summary = {severity: 0 for severity in SEVERITY_WEIGHT}
    for item in findings:
        summary[item.severity] += 1
    penalty = sum(summary[severity] * weight for severity, weight in SEVERITY_WEIGHT.items())
    return AuditReport(
        tenant=inventory["tenant"],
        generated_at=now.isoformat(),
        inventory_generated_at=inventory["generated_at"],
        findings=tuple(findings),
        secure_score=max(0, 100 - penalty),
        summary=summary,
    )
