#Requires -Version 5.1
<#
.SYNOPSIS
    Uninstalls the HEIC to JPG Converter sparse package.
.DESCRIPTION
    Removes the sparse package registration so "Convert to JPG" is no longer
    shown in the Windows 11 right-click context menu for .heic / .heif files.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$pkg = Get-AppxPackage -Name 'HeicToJpgConverter' -ErrorAction SilentlyContinue

if ($pkg) {
    Write-Host "Removing package: $($pkg.PackageFullName)" -ForegroundColor Cyan
    Remove-AppxPackage -Package $pkg.PackageFullName
    Write-Host ""
    Write-Host "Uninstalled. 'Convert to JPG' has been removed from the context menu." -ForegroundColor Green

    # Clean up the generated msix file
    $msixPath = Join-Path $PSScriptRoot 'HeicConverter.msix'
    if (Test-Path $msixPath) {
        Remove-Item $msixPath -Force
        Write-Host "Removed HeicConverter.msix" -ForegroundColor Gray
    }
} else {
    Write-Host "Package 'HeicToJpgConverter' is not installed — nothing to uninstall." -ForegroundColor Yellow
}
