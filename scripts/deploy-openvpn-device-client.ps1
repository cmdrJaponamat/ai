#requires -Version 5.1
<#
.SYNOPSIS
  Updates OpenVPN Community Edition and grants its automatic service read access
  to this computer's AD CS client-authentication private key.
.DESCRIPTION
  Run elevated or as LocalSystem from an RMM or a computer GPO. The MSI is copied
  locally before installation so an existing VPN can disconnect during upgrade.
  Re-run after certificate renewal to grant access to the new key container.
  Supports Microsoft Software KSP (CNG) and Microsoft RSA CSP machine keys.
.EXAMPLE
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\deploy-openvpn-device-client.ps1 `
    -MsiPath '\\aurora-logistics.local\SYSVOL\aurora-logistics.local\software\OpenVPN-2.7.8-I001-amd64.msi' `
    -TargetVersion '2.7.8' `
    -ExpectedSha256 '<SHA256 of the approved MSI>'
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $MsiPath,

    [Parameter(Mandatory = $true)]
    [version] $TargetVersion,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-fA-F]{64}$')]
    [string] $ExpectedSha256,

    [string] $DomainSuffix = 'aurora-logistics.local',
    [string] $IssuerCommonName = 'AL-ISSUING-CA'
)

$ErrorActionPreference = 'Stop'
$serviceName = 'OpenVPNService'
$serviceAccount = 'NT SERVICE\OpenVPNService'
$clientAuthOid = '1.3.6.1.5.5.7.3.2'
$computerFqdn = "$($env:COMPUTERNAME).$DomainSuffix"
$subjectPattern = '(^|,\s*)CN=' + [regex]::Escape($computerFqdn) + '(,|$)'

function Get-InstalledOpenVpnVersion {
    $exe = Join-Path $env:ProgramFiles 'OpenVPN\bin\openvpn.exe'
    if (-not (Test-Path -LiteralPath $exe)) { return [version] '0.0' }
    $raw = (Get-Item -LiteralPath $exe).VersionInfo.ProductVersion
    if ($raw -notmatch '^\d+(?:\.\d+){1,3}') {
        throw "Cannot determine installed OpenVPN version from $exe : $raw"
    }
    return [version] $Matches[0]
}

function Test-ClientAuthenticationEku {
    param([System.Security.Cryptography.X509Certificates.X509Certificate2] $Certificate)
    $extension = $Certificate.Extensions |
        Where-Object { $_.Oid.Value -eq '2.5.29.37' } |
        Select-Object -First 1
    if ($null -eq $extension) { return $false }
    $eku = [System.Security.Cryptography.X509Certificates.X509EnhancedKeyUsageExtension]::new(
        $extension, $extension.Critical
    )
    return @($eku.EnhancedKeyUsages | Where-Object { $_.Value -eq $clientAuthOid }).Count -gt 0
}

function Get-MachineKeyPath {
    param([System.Security.Cryptography.X509Certificates.X509Certificate2] $Certificate)
    $rsa = [System.Security.Cryptography.X509Certificates.RSACertificateExtensions]::GetRSAPrivateKey($Certificate)
    if ($null -eq $rsa) { throw "Certificate $($Certificate.Thumbprint) has no usable RSA private key" }
    try {
        if ($rsa -is [System.Security.Cryptography.RSACng]) {
            if ($rsa.Key.Provider.Provider -ne 'Microsoft Software Key Storage Provider' -or
                -not $rsa.Key.IsMachineKey) {
                throw "Certificate $($Certificate.Thumbprint) uses a non-software or non-machine CNG key; inspect its provider"
            }
            return Join-Path $env:ProgramData ("Microsoft\Crypto\Keys\" + $rsa.Key.UniqueName)
        }
        if ($rsa -is [System.Security.Cryptography.RSACryptoServiceProvider]) {
            if (-not $rsa.CspKeyContainerInfo.MachineKeyStore) {
                throw "Certificate $($Certificate.Thumbprint) has a user-scope CSP key"
            }
            return Join-Path $env:ProgramData (
                "Microsoft\Crypto\RSA\MachineKeys\" + $rsa.CspKeyContainerInfo.UniqueKeyContainerName
            )
        }
        throw "Unsupported RSA provider for certificate $($Certificate.Thumbprint): $($rsa.GetType().FullName)"
    }
    finally { $rsa.Dispose() }
}

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if ($identity.User.Value -ne 'S-1-5-18' -and
    -not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run this script elevated or as LocalSystem.'
}

# A computer certificate may overlap with its renewed replacement. Grant only
# currently valid certificates with the expected subject, issuer and EKU.
$now = Get-Date
$certificates = @(Get-ChildItem Cert:\LocalMachine\My | Where-Object {
    $_.HasPrivateKey -and $_.NotBefore -le $now -and $_.NotAfter -gt $now -and
    $_.Subject -match $subjectPattern -and
    $_.Issuer -match ('(^|,\s*)CN=' + [regex]::Escape($IssuerCommonName) + '(,|$)') -and
    (Test-ClientAuthenticationEku $_)
})
if ($certificates.Count -eq 0) {
    throw "No valid machine client-authentication certificate for $computerFqdn from $IssuerCommonName. Enroll it before upgrading OpenVPN."
}

if (-not (Get-Service -Name $serviceName -ErrorAction SilentlyContinue)) {
    throw "$serviceName is absent; this script is for updating an installed client."
}

$serviceSid = [Security.Principal.NTAccount]::new($serviceAccount).Translate(
    [Security.Principal.SecurityIdentifier]
)
$keyAclChanged = $false
foreach ($certificate in $certificates) {
    $keyPath = Get-MachineKeyPath $certificate
    if (-not (Test-Path -LiteralPath $keyPath -PathType Leaf)) {
        throw "Private key file not found for $($certificate.Thumbprint): $keyPath"
    }
    $existingRules = (Get-Acl -LiteralPath $keyPath).GetAccessRules(
        $true, $false, [Security.Principal.SecurityIdentifier]
    )
    $hasRead = @($existingRules | Where-Object {
        $_.IdentityReference.Value -eq $serviceSid.Value -and
        $_.AccessControlType -eq [Security.AccessControl.AccessControlType]::Allow -and
        ($_.FileSystemRights -band [Security.AccessControl.FileSystemRights]::ReadData) -ne 0
    }).Count -gt 0
    if ($hasRead) {
        Write-Output "KEY_READ_ALREADY_PRESENT thumbprint=$($certificate.Thumbprint)"
        continue
    }
    & icacls.exe $keyPath '/grant:r' "${serviceAccount}:R" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to grant $serviceAccount read access to key for $($certificate.Thumbprint)"
    }
    $keyAclChanged = $true
    Write-Output "KEY_READ_OK thumbprint=$($certificate.Thumbprint)"
}

$installedVersion = Get-InstalledOpenVpnVersion
$rebootRequired = $false
if ($installedVersion -lt $TargetVersion) {
    if (-not (Test-Path -LiteralPath $MsiPath -PathType Leaf)) {
        throw "MSI is unavailable: $MsiPath"
    }
    $stagedMsi = Join-Path $env:TEMP ('openvpn-approved-' + [guid]::NewGuid().ToString('N') + '.msi')
    try {
        Copy-Item -LiteralPath $MsiPath -Destination $stagedMsi -ErrorAction Stop
        $actualSha256 = (Get-FileHash -LiteralPath $stagedMsi -Algorithm SHA256).Hash
        if ($actualSha256 -ne $ExpectedSha256) {
            throw "MSI SHA-256 mismatch. Expected $ExpectedSha256; got $actualSha256"
        }
        $signature = Get-AuthenticodeSignature -LiteralPath $stagedMsi
        if ($signature.Status -ne 'Valid') {
            throw "MSI Authenticode signature is not valid: $($signature.Status)"
        }
        $msiArguments = '/i "{0}" /qn /norestart ALLUSERS=1' -f $stagedMsi
        $process = Start-Process -FilePath msiexec.exe -ArgumentList $msiArguments -Wait -PassThru
        if ($process.ExitCode -notin @(0, 3010)) {
            throw "msiexec failed with exit code $($process.ExitCode)"
        }
        $rebootRequired = ($process.ExitCode -eq 3010)
        $afterVersion = Get-InstalledOpenVpnVersion
        if ($afterVersion -lt $TargetVersion -and -not $rebootRequired) {
            throw "OpenVPN version is $afterVersion after MSI, expected at least $TargetVersion"
        }
        Write-Output "OPENVPN_UPDATED from=$installedVersion to=$afterVersion"
    }
    finally {
        if (Test-Path -LiteralPath $stagedMsi) {
            Remove-Item -LiteralPath $stagedMsi -Force
        }
    }
}
else {
    Write-Output "OPENVPN_ALREADY_CURRENT version=$installedVersion"
}

Set-Service -Name $serviceName -StartupType Automatic
$service = Get-Service -Name $serviceName
if ($service.Status -ne 'Running') {
    Start-Service -Name $serviceName
}
elseif (($installedVersion -lt $TargetVersion -or $keyAclChanged) -and -not $rebootRequired) {
    Restart-Service -Name $serviceName
}
Write-Output "SERVICE_STATUS=$((Get-Service -Name $serviceName).Status)"
if ($rebootRequired) {
    Write-Warning 'The MSI requested a reboot. Schedule it after the deployment wave.'
    exit 3010
}
exit 0
