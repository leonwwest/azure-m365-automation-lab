import json
from pathlib import Path

from tenant_guard.cli import main

SAMPLE = Path(__file__).parents[1] / "inventory" / "sample-tenant.json"


def test_cli_writes_complete_report_bundle(tmp_path: Path) -> None:
    assert main([str(SAMPLE), "--output", str(tmp_path), "--fail-on", "never"]) == 0
    assert {path.name for path in tmp_path.iterdir()} == {
        "audit-report.json",
        "audit-report.md",
        "remediation-plan.json",
    }
    report = json.loads((tmp_path / "audit-report.json").read_text())
    assert report["tenant"] == "contoso-lab.onmicrosoft.com"
    assert report["findings"]


def test_cli_can_gate_on_high_findings(tmp_path: Path) -> None:
    assert main([str(SAMPLE), "--output", str(tmp_path), "--fail-on", "high"]) == 2

