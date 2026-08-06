[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PlanPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$plan = Get-Content -Path $PlanPath -Raw | ConvertFrom-Json
if ($plan.mode -ne 'dry-run') {
    throw 'Only dry-run remediation plans are accepted.'
}

$plan.actions | Sort-Object severity, rule_id | Format-Table `
    action_id, severity, rule_id, resource, status -AutoSize

Write-Host ''
Write-Host 'No tenant or subscription changes were made.'
Write-Host 'Every action remains proposed and requires an approved change workflow.'

