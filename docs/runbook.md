# Governance review runbook

## 1. Prepare an inventory

Use `inventory/sample-tenant.json` for the portfolio demonstration. In an authorized tenant,
run `powershell/Export-SanitizedInventory.ps1` with read-only Graph scopes and keep the raw
file under `inventory/private/`, which is ignored by Git.

Before sharing an export, verify that it contains no UPNs, e-mail addresses, object IDs,
credential values, IP addresses or customer names.

## 2. Run the audit

```bash
python -m tenant_guard.cli inventory/sample-tenant.json \
  --output reports/latest \
  --fail-on critical
```

Exit code `2` means the configured quality gate found the chosen severity. The report is still
written so CI and operators have evidence.

## 3. Triage findings

Work in this order:

1. expired credentials and privileged identities without MFA;
2. public endpoints and missing Conditional Access coverage;
3. inactive privileged identities and missing diagnostics;
4. ownership, guest recertification, licensing and tags.

Validate each finding against business context. A rule is a decision aid, not permission to
change a tenant.

## 4. Review the plan

```powershell
./powershell/Review-RemediationPlan.ps1 -PlanPath reports/latest/remediation-plan.json
```

The plan contains only proposed actions. Record owner, rollback, maintenance window and approval
in the organization's normal change process before implementation.

## 5. Verify and close

Re-export the inventory after an approved change, rerun the audit and attach both reports to the
change record. A finding is closed only when the new evidence proves the desired state.

