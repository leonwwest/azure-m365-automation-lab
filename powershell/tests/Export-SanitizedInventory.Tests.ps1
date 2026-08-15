Describe 'Export-SanitizedInventory' {
    BeforeAll {
        function Connect-MgGraph {}
        function Get-MgContext {}
        function Get-MgUser {}
        function Get-MgServicePrincipal {}
        function Get-MgIdentityConditionalAccessPolicy {}
    }

    BeforeEach {
        Mock Connect-MgGraph {}
        Mock Get-MgContext { [pscustomobject]@{ TenantId = '11111111-2222-3333-4444-555555555555' } }
        Mock Get-MgUser {
            [pscustomobject]@{
                Id = 'private-object-id'
                DisplayName = 'Synthetic Admin'
                UserPrincipalName = 'private@example.invalid'
                Mail = 'private@example.invalid'
                UserType = 'Member'
                AccountEnabled = $true
                AssignedLicenses = @([pscustomobject]@{ SkuId = 'private-sku-id' })
            }
        }
        Mock Get-MgServicePrincipal { @() }
        Mock Get-MgIdentityConditionalAccessPolicy { @() }
    }

    It 'uses only documented read-only Graph scopes' {
        $output = Join-Path $TestDrive 'inventory.json'
        & "$PSScriptRoot/../Export-SanitizedInventory.ps1" -OutputPath $output

        Should -Invoke Connect-MgGraph -Times 1 -ParameterFilter {
            $Scopes.Count -eq 5 -and
            ($Scopes | Where-Object { $_ -notmatch '\.Read\.All$' }).Count -eq 0
        }
    }

    It 'omits identifiers, addresses and credential values from the public contract' {
        $output = Join-Path $TestDrive 'inventory.json'
        & "$PSScriptRoot/../Export-SanitizedInventory.ps1" -OutputPath $output
        $raw = Get-Content $output -Raw
        $inventory = $raw | ConvertFrom-Json

        $inventory.schema_version | Should -Be '1.0.0'
        $raw | Should -Not -Match 'private-object-id|private@example.invalid|private-sku-id'
        $inventory.users[0].PSObject.Properties.Name | Should -Not -Contain 'id'
        $inventory.users[0].PSObject.Properties.Name | Should -Not -Contain 'mail'
        $inventory.users[0].PSObject.Properties.Name | Should -Not -Contain 'user_principal_name'
    }
}
