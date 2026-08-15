[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host 'Connecting with read-only Microsoft Graph scopes...'
Connect-MgGraph -Scopes @(
    'User.Read.All',
    'Directory.Read.All',
    'Policy.Read.All',
    'Application.Read.All',
    'AuditLog.Read.All'
) -NoWelcome

$context = Get-MgContext
$users = Get-MgUser -All -Property Id,DisplayName,AccountEnabled,UserType,AssignedLicenses
$servicePrincipals = Get-MgServicePrincipal -All -Property Id,DisplayName,PasswordCredentials
$policies = Get-MgIdentityConditionalAccessPolicy -All

# This export deliberately omits UPNs, mail addresses, object IDs and credential values.
$inventory = [ordered]@{
    schema_version = '1.0.0'
    tenant = "tenant-$($context.TenantId.Substring(0, 8))"
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    users = @($users | ForEach-Object {
        [ordered]@{
            display_name = $_.DisplayName
            user_type = $_.UserType
            enabled = $_.AccountEnabled
            is_privileged = $false
            mfa_registered = $false
            break_glass = $false
            last_sign_in_at = $null
            licenses = @($_.AssignedLicenses | ForEach-Object { 'assigned-license' })
        }
    })
    service_principals = @($servicePrincipals | ForEach-Object {
        $expiry = $_.PasswordCredentials | Sort-Object EndDateTime | Select-Object -First 1
        [ordered]@{
            display_name = $_.DisplayName
            owners = @()
            credential_expires_at = if ($expiry) { $expiry.EndDateTime } else { $null }
        }
    })
    conditional_access_policies = @($policies | ForEach-Object {
        [ordered]@{
            display_name = $_.DisplayName
            state = [string]$_.State
            grant_controls = @($_.GrantControls.BuiltInControls | ForEach-Object { $_.ToLowerInvariant() })
        }
    })
    azure_resources = @()
}

$directory = Split-Path -Parent $OutputPath
if ($directory) {
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
}
$inventory | ConvertTo-Json -Depth 8 | Set-Content -Path $OutputPath -Encoding utf8
Write-Host "Sanitized inventory written to $OutputPath"
Write-Warning 'Review the export before moving it outside inventory/private/.'
