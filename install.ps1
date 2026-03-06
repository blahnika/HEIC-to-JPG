#Requires -Version 5.1
<#
.SYNOPSIS
    Installs the HEIC to JPG Converter sparse package for Windows 11 context menu support.
.DESCRIPTION
    This script:
      1. Builds launcher.exe from source (requires .NET 8 SDK)
      2. Creates a self-signed code-signing certificate
      3. Trusts the certificate for the current user
      4. Packages and signs the sparse MSIX manifest
      5. Registers the sparse package so "Convert to JPG" appears in the
         Windows 11 right-click menu when selecting .heic or .heif files
.NOTES
    Prerequisites:
      - Windows 10 20H1 (build 19041) or later / Windows 11
      - .NET 8 SDK  https://dotnet.microsoft.com/download
      - Windows SDK (makeappx.exe + signtool.exe)
          Install via Visual Studio Installer > Individual Components
          or the standalone Windows SDK from https://developer.microsoft.com/windows/downloads/windows-sdk/
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = $PSScriptRoot

# -- Helper --------------------------------------------------------------------

function Find-SDKTool {
    param([string]$ToolName)
    $kitsReg = Get-ItemProperty `
        'HKLM:\SOFTWARE\Microsoft\Windows Kits\Installed Roots' `
        -ErrorAction SilentlyContinue
    $sdkRoot = if ($kitsReg -and ($kitsReg.PSObject.Properties['KitsRoot10'])) { $kitsReg.KitsRoot10 } else { $null }
    if (-not $sdkRoot) { return $null }
    # Search bin\ (versioned SDK layout) and App Certification Kit\ (flat layout)
    $searchRoots = @("$sdkRoot\bin", "$sdkRoot\App Certification Kit")
    $candidates = $searchRoots | ForEach-Object {
        Get-ChildItem $_ -Filter $ToolName -Recurse -ErrorAction SilentlyContinue
    } | Where-Object { $_.FullName -notmatch 'arm' -and ($_.FullName -match 'x64' -or $_.DirectoryName -notmatch '\\(x86|arm)') } |
        Sort-Object FullName -Descending
    return $candidates | Select-Object -First 1 -ExpandProperty FullName
}

# -- Step 1: Build launcher.exe -----------------------------------------------

Write-Host ""
Write-Host "=== Step 1/5: Building launcher.exe ===" -ForegroundColor Cyan

$launcherExe = Join-Path $repoRoot 'launcher.exe'
$launcherProject = Join-Path $repoRoot 'src\Launcher\Launcher.csproj'

if (Test-Path $launcherExe) {
    Write-Host "  launcher.exe already exists, skipping build." -ForegroundColor Gray
} else {
    if (-not (Get-Command 'dotnet' -ErrorAction SilentlyContinue)) {
        Write-Error @"
  .NET 8 SDK not found. Please install it from:
  https://dotnet.microsoft.com/download/dotnet/8.0
  Then re-run this script.
"@
    }
    Write-Host "  Running: dotnet publish ..."
    & dotnet publish $launcherProject `
        -r win-x64 `
        -p:PublishSingleFile=true `
        -p:SelfContained=false `
        --output $repoRoot `
        --configuration Release `
        --nologo -v quiet
    if ($LASTEXITCODE -ne 0) { throw "dotnet publish failed." }
    Write-Host "  launcher.exe built successfully." -ForegroundColor Green
}

# -- Step 2: Create self-signed certificate -----------------------------------

Write-Host ""
Write-Host "=== Step 2/5: Creating self-signed certificate ===" -ForegroundColor Cyan

$certSubject = 'CN=HeicConverter'
$existingCert = Get-ChildItem 'Cert:\CurrentUser\My' |
    Where-Object { $_.Subject -eq $certSubject } |
    Sort-Object NotAfter -Descending |
    Select-Object -First 1

if ($existingCert -and $existingCert.NotAfter -gt (Get-Date)) {
    Write-Host "  Existing certificate found, reusing it." -ForegroundColor Gray
    $cert = $existingCert
} else {
    $cert = New-SelfSignedCertificate `
        -Subject $certSubject `
        -CertStoreLocation 'Cert:\CurrentUser\My' `
        -Type CodeSigningCert `
        -KeyUsage DigitalSignature `
        -FriendlyName 'HEIC to JPG Converter' `
        -NotAfter (Get-Date).AddYears(10)
    Write-Host "  Certificate created (thumbprint: $($cert.Thumbprint))" -ForegroundColor Green
}

# -- Step 3: Trust the certificate (current user, no admin needed) ------------

Write-Host ""
Write-Host "=== Step 3/5: Trusting the certificate ===" -ForegroundColor Cyan

$certFile = Join-Path $env:TEMP 'HeicConverter.cer'
Export-Certificate -Cert $cert -FilePath $certFile -Force | Out-Null
$alreadyTrusted = Get-ChildItem 'Cert:\CurrentUser\Root' |
    Where-Object { $_.Thumbprint -eq $cert.Thumbprint }
if ($alreadyTrusted) {
    Write-Host "  Certificate already trusted." -ForegroundColor Gray
} else {
    Import-Certificate -FilePath $certFile -CertStoreLocation 'Cert:\CurrentUser\Root' | Out-Null
    Write-Host "  Certificate trusted for current user." -ForegroundColor Green
}
Remove-Item $certFile -Force -ErrorAction SilentlyContinue

# -- Step 4: Build and sign the MSIX sparse package ---------------------------

Write-Host ""
Write-Host "=== Step 4/5: Building and signing sparse MSIX package ===" -ForegroundColor Cyan

$makeappx = Find-SDKTool 'makeappx.exe'
$signtool  = Find-SDKTool 'signtool.exe'

if (-not $makeappx) {
    Write-Error @"
  makeappx.exe not found. Install the Windows SDK:
    - Via Visual Studio Installer > Individual Components > 'Windows SDK'
    - Or standalone: https://developer.microsoft.com/windows/downloads/windows-sdk/
  Then re-run this script.
"@
}
if (-not $signtool) {
    Write-Error @"
  signtool.exe not found (should be in the same Windows SDK installation as makeappx.exe).
"@
}

$sparseDir = Join-Path $repoRoot 'sparse-package'
$msixPath  = Join-Path $repoRoot 'HeicConverter.msix'

if (Test-Path $msixPath) { Remove-Item $msixPath -Force }

Write-Host "  Packing sparse package..."
& $makeappx pack /d $sparseDir /p $msixPath /nv 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { throw "makeappx failed." }

# The 2013-era makeappx compresses AppxManifest.xml, which violates the MSIX
# spec (metadata files must be stored uncompressed).  Repack to fix this.
# Python (Windows Store) can't write to OneDrive paths, so stage via %TEMP%.
Write-Host "  Fixing MSIX compression (stored metadata)..."
$repackScript = Join-Path $repoRoot 'repack_msix.py'
$msixTempIn  = Join-Path $env:TEMP 'HeicConverter_in.msix'
$msixTempOut = Join-Path $env:TEMP 'HeicConverter_out.msix'
Copy-Item $msixPath $msixTempIn -Force
& python $repackScript $msixTempIn $msixTempOut
if ($LASTEXITCODE -ne 0) { throw "repack_msix.py failed." }
Copy-Item $msixTempOut $msixPath -Force
Remove-Item $msixTempIn, $msixTempOut -Force -ErrorAction SilentlyContinue

Write-Host "  Signing with certificate..."
& $signtool sign /fd SHA256 /sha1 $cert.Thumbprint $msixPath 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { throw "signtool failed." }

Write-Host "  Package built and signed." -ForegroundColor Green

# -- Step 5: Register the sparse package --------------------------------------

Write-Host ""
Write-Host "=== Step 5/5: Registering sparse package ===" -ForegroundColor Cyan

# Remove existing registration if present
$existingPkg = Get-AppxPackage -Name 'HeicToJpgConverter' -ErrorAction SilentlyContinue
if ($existingPkg) {
    Write-Host "  Removing previous registration..."
    Remove-AppxPackage -Package $existingPkg.PackageFullName
}

Add-AppxPackage -Path $msixPath -ExternalLocation $repoRoot

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host " Installation complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host " Right-click any .heic or .heif file and select"
Write-Host " 'Convert to JPG' - it will appear directly in"
Write-Host " the Windows 11 context menu."
Write-Host ""
Write-Host " To uninstall, run: .\uninstall.ps1"
Write-Host ""
