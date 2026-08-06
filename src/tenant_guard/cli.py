"""Command-line interface for the governance audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tenant_guard.audit import SEVERITY_ORDER, audit_inventory
from tenant_guard.reporting import write_report_bundle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit a sanitized Azure/M365 inventory.")
    parser.add_argument("inventory", type=Path, help="path to the sanitized JSON inventory")
    parser.add_argument("--output", type=Path, default=Path("reports/latest"))
    parser.add_argument(
        "--fail-on",
        choices=("critical", "high", "medium", "low", "never"),
        default="critical",
        help="return exit code 2 when this severity or higher is present",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    report = audit_inventory(inventory)
    paths = write_report_bundle(report, args.output)
    print(
        f"tenant={report.tenant} score={report.secure_score} "
        f"findings={len(report.findings)} output={args.output}"
    )
    for path in paths:
        print(path)
    if args.fail_on == "never":
        return 0
    threshold = SEVERITY_ORDER[args.fail_on]
    if any(SEVERITY_ORDER[finding.severity] <= threshold for finding in report.findings):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

