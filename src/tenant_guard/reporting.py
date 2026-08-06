"""JSON, Markdown and remediation-plan renderers."""

from __future__ import annotations

import json
from pathlib import Path

from tenant_guard.audit import AuditReport


def remediation_plan(report: AuditReport) -> dict:
    return {
        "mode": "dry-run",
        "tenant": report.tenant,
        "generated_at": report.generated_at,
        "actions": [
            {
                "action_id": f"action-{index:03d}",
                "rule_id": finding.rule_id,
                "severity": finding.severity,
                "resource": finding.resource,
                "proposed_change": finding.recommendation,
                "approval_required": True,
                "status": "proposed",
            }
            for index, finding in enumerate(report.findings, start=1)
        ],
    }


def render_markdown(report: AuditReport) -> str:
    rows = [
        "# Azure & Microsoft 365 Governance Report",
        "",
        f"- Tenant: `{report.tenant}`",
        f"- Inventory generated: `{report.inventory_generated_at}`",
        f"- Audit generated: `{report.generated_at}`",
        f"- Demonstration score: **{report.secure_score}/100**",
        "",
        "The score is a transparent portfolio heuristic, not Microsoft Secure Score.",
        "",
        "## Summary",
        "",
        "| Severity | Findings |",
        "|---|---:|",
    ]
    rows.extend(f"| {severity.title()} | {count} |" for severity, count in report.summary.items())
    rows.extend(["", "## Findings", ""])
    if not report.findings:
        rows.append("No findings.")
    for index, finding in enumerate(report.findings, start=1):
        rows.extend(
            [
                f"### {index}. [{finding.severity.upper()}] {finding.title}",
                "",
                f"- Rule: `{finding.rule_id}`",
                f"- Resource: `{finding.resource}`",
                f"- Evidence: {finding.evidence}",
                f"- Recommended next step: {finding.recommendation}",
                "",
            ]
        )
    rows.extend(
        [
            "## Safety boundary",
            "",
            "This report was produced from a sanitized export. The generated remediation plan is",
            "dry-run only and every proposed change requires human approval.",
            "",
        ]
    )
    return "\n".join(rows)


def write_report_bundle(report: AuditReport, output_dir: Path) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "audit-report.json"
    markdown_path = output_dir / "audit-report.md"
    plan_path = output_dir / "remediation-plan.json"
    json_path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    plan_path.write_text(json.dumps(remediation_plan(report), indent=2) + "\n", encoding="utf-8")
    return json_path, markdown_path, plan_path

