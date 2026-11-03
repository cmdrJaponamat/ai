#requires -Version 5.1
<#
.SYNOPSIS
  Updates OpenVPN Community Edition, installs its automatic profile and grants
  the service read access to this computer's AD CS private key.
.DESCRIPTION
  Run elevated or as LocalSystem from an RMM or a computer GPO. The MSI is copied
  locally before installation so an existing VPN can disconnect during upgrade.
  Re-run after certificate renewal to grant access to the new key container.
  Supports Microsoft Software KSP (CNG) and Microsoft RSA CSP machine keys.
  The approved profile template must contain {{COMPUTER_FQDN}} in cryptoapicert.
.EXAMPLE
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\deploy-openvpn-device-client.ps1 `
    -MsiPath '\\aurora-logistics.local\SYSVOL\aurora-logistics.local\software\OpenVPN-2.7.8-I001-amd64.msi' `
    -TargetVersion '2.7.8' `
    -ExpectedSha256 '<SHA256 of the approved MSI>' `
    -ProfileTemplatePath '\\aurora-logistics.local\SYSVOL\aurora-logistics.local\software\openvpn-device.ovpn.tmpl' `
    -ExpectedProfileSha256 '<SHA256 of the approved template>'
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

    [Parameter(Mandatory = $true)]
    [string] $ProfileTemplatePath,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-fA-F]{64}$')]
    [string] $ExpectedProfileSha256,

    [string] $ProfileName = 'device.ovpn',
    [string] $DomainSuffix = 'aurora-logistics.local',
    [string] $IssuerCommonName = 'AL-ISSUING-CA'
)

$ErrorActionPreference = 'Stop'
$serviceName = 'OpenVPNService'
$serviceAccount = 'NT SERVICE\OpenVPNService'
$clientAuthOid = '1.3.6.1.5.5.7.3.2'
$computerFqdn = "$($env:COMPUTERNAME).$DomainSuffix"
$subjectPattern = '(^|,\s*)CN=' + [regex]::Escape($computerFqdn) + '(,|$)'
if ($ProfileName -notmatch '^[A-Za-z0-9._-]+\.ovpn$') {
    throw "Invalid profile name: $ProfileName"
}

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

if (-not (Test-Path -LiteralPath $ProfileTemplatePath -PathType Leaf)) {
    throw "Profile template is unavailable: $ProfileTemplatePath"
}
$stagedTemplate = Join-Path $env:TEMP (
    'openvpn-profile-' + [guid]::NewGuid().ToString('N') + '.tmpl'
)
try {
    Copy-Item -LiteralPath $ProfileTemplatePath -Destination $stagedTemplate -ErrorAction Stop
    $actualProfileSha256 = (Get-FileHash -LiteralPath $stagedTemplate -Algorithm SHA256).Hash
    if ($actualProfileSha256 -ne $ExpectedProfileSha256) {
        throw "Profile template SHA-256 mismatch. Expected $ExpectedProfileSha256; got $actualProfileSha256"
    }
    $strictUtf8 = [Text.UTF8Encoding]::new($false, $true)
    $templateText = [IO.File]::ReadAllText($stagedTemplate, $strictUtf8)
}
finally {
    if (Test-Path -LiteralPath $stagedTemplate) {
        Remove-Item -LiteralPath $stagedTemplate -Force
    }
}
if ($templateText -notmatch '(?im)^\s*cryptoapicert\s+.*\{\{COMPUTER_FQDN\}\}') {
    throw 'Profile template must select the machine certificate using {{COMPUTER_FQDN}} in cryptoapicert.'
}
if ($templateText -match '(?im)^\s*(auth-user-pass|key|pkcs12)\b|<key>') {
    throw 'Profile template must use the machine certificate without an embedded private key or user password.'
}
$profileText = $templateText.Replace('{{COMPUTER_FQDN}}', $computerFqdn)

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

$profileDirectory = Join-Path $env:ProgramFiles 'OpenVPN\config-auto'
if (-not (Test-Path -LiteralPath $profileDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $profileDirectory -Force | Out-Null
}
$otherProfiles = @(Get-ChildItem -LiteralPath $profileDirectory -Filter '*.ovpn' -File |
    Where-Object { $_.Name -ne $ProfileName })
if ($otherProfiles.Count -gt 0) {
    Write-Warning ("Other automatic OpenVPN profiles remain enabled: " +
        (($otherProfiles | ForEach-Object Name) -join ', '))
}
$profileDestination = Join-Path $profileDirectory $ProfileName
$utf8 = [Text.UTF8Encoding]::new($false)
$profileBytes = $utf8.GetBytes($profileText)
$profileSha256 = [BitConverter]::ToString(
    [Security.Cryptography.SHA256]::Create().ComputeHash($profileBytes)
).Replace('-', '')
$profileChanged = -not (Test-Path -LiteralPath $profileDestination -PathType Leaf)
if (-not $profileChanged) {
    $profileChanged = (Get-FileHash -LiteralPath $profileDestination -Algorithm SHA256).Hash -ne $profileSha256
}
if ($profileChanged) {
    $temporaryProfile = Join-Path $profileDirectory (
        '.' + $ProfileName + '.' + [guid]::NewGuid().ToString('N') + '.tmp'
    )
    try {
        if (Test-Path -LiteralPath $profileDestination -PathType Leaf) {
            $backupPath = Join-Path $profileDirectory (
                $ProfileName + '.before-' + (Get-Date -Format 'yyyyMMdd-HHmmss') +
                '-' + [guid]::NewGuid().ToString('N') + '.bak'
            )
            [IO.File]::WriteAllBytes($backupPath, [IO.File]::ReadAllBytes($profileDestination))
            & icacls.exe $backupPath '/inheritance:r' | Out-Null
            if ($LASTEXITCODE -ne 0) { throw "Failed to secure backup $backupPath" }
            $serviceReadAce = '*' + $serviceSid.Value + ':R'
            & icacls.exe $backupPath '/grant:r' '*S-1-5-18:F' '*S-1-5-32-544:F' $serviceReadAce | Out-Null
            if ($LASTEXITCODE -ne 0) { throw "Failed to secure backup $backupPath" }
            Write-Output "PROFILE_BACKUP path=$backupPath"
        }
        [IO.File]::WriteAllBytes($temporaryProfile, $profileBytes)
        & icacls.exe $temporaryProfile '/inheritance:r' | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Failed to remove inherited ACL from $temporaryProfile" }
        $serviceReadAce = '*' + $serviceSid.Value + ':R'
        & icacls.exe $temporaryProfile '/grant:r' '*S-1-5-18:F' '*S-1-5-32-544:F' $serviceReadAce | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Failed to secure $temporaryProfile" }
        Move-Item -LiteralPath $temporaryProfile -Destination $profileDestination -Force
    }
    finally {
        if (Test-Path -LiteralPath $temporaryProfile) {
            Remove-Item -LiteralPath $temporaryProfile -Force
        }
    }
    Write-Output "PROFILE_UPDATED path=$profileDestination"
}
else {
    Write-Output "PROFILE_ALREADY_CURRENT path=$profileDestination"
}

Set-Service -Name $serviceName -StartupType Automatic
$service = Get-Service -Name $serviceName
if ($service.Status -ne 'Running') {
    Start-Service -Name $serviceName
}
elseif (($installedVersion -lt $TargetVersion -or $keyAclChanged -or $profileChanged) -and -not $rebootRequired) {
    Restart-Service -Name $serviceName
}
Write-Output "SERVICE_STATUS=$((Get-Service -Name $serviceName).Status)"
if ($rebootRequired) {
    Write-Warning 'The MSI requested a reboot. Schedule it after the deployment wave.'
    exit 3010
}
exit 0
