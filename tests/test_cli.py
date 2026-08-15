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


def test_cli_rejects_incompatible_inventory_with_field_path(
    tmp_path: Path, capsys
) -> None:
    inventory = json.loads(SAMPLE.read_text())
    inventory["users"][0]["enabled"] = "yes"
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps(inventory))

    assert main([str(invalid), "--output", str(tmp_path / "report")]) == 3
    output = capsys.readouterr().out
    assert "Inventory validation failed" in output
    assert "users.0.enabled" in output


def test_committed_sample_matches_versioned_schema() -> None:
    from tenant_guard.inventory_schema import validate_inventory

    assert validate_inventory(json.loads(SAMPLE.read_text())) == []
