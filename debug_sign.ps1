param([string]$RepoRoot = $PSScriptRoot)

Add-Type -AssemblyName System.IO.Compression.FileSystem

$kitsReg  = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows Kits\Installed Roots' -ErrorAction SilentlyContinue
$sdkRoot  = $kitsReg.KitsRoot10
$searchRoots = @("$sdkRoot\bin", "$sdkRoot\App Certification Kit")
$signtool = $searchRoots | ForEach-Object {
    Get-ChildItem $_ -Filter signtool.exe -Recurse -ErrorAction SilentlyContinue
} | Where-Object { $_.FullName -notmatch 'arm' -and ($_.FullName -match 'x64' -or $_.DirectoryName -notmatch '\\(x86|arm)') } |
    Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName

$cert = Get-ChildItem 'Cert:\CurrentUser\My' |
    Where-Object { $_.Subject -eq 'CN=HeicConverter' } |
    Sort-Object NotAfter -Descending | Select-Object -First 1

# ── Test 1: SIP registry - is .msix registered? ──────────────────────────────
Write-Host "=== SIP registry ==="
$sipBase = 'HKLM:\SOFTWARE\Microsoft\Cryptography\OID\EncodingType 0\CryptSIPDllIsMyFileType2'
foreach ($ext in @('.msix', '.appx', '.appxbundle')) {
    $key = Join-Path $sipBase $ext
    $val = Get-ItemProperty $key -ErrorAction SilentlyContinue
    if ($val) {
        Write-Host "  $ext -> DLL=$($val.Dll) Func=$($val.FuncName)"
    } else {
        Write-Host "  $ext -> NOT REGISTERED"
    }
}
Write-Host ""

# ── Test 2: Try signing as .appx ─────────────────────────────────────────────
Write-Host "=== Test: Sign as .appx ==="
$appxPath = Join-Path $env:TEMP 'HeicConverter_test.appx'
Copy-Item (Join-Path $RepoRoot 'HeicConverter.msix') $appxPath -Force
& $signtool sign /fd SHA256 /sha1 $cert.Thumbprint $appxPath
Write-Host "exit: $LASTEXITCODE"
Write-Host ""

# ── Test 3: Dump first 64 bytes of the MSIX (ZIP magic + first LFH) ──────────
Write-Host "=== Raw ZIP header bytes ==="
$bytes = [System.IO.File]::ReadAllBytes((Join-Path $RepoRoot 'HeicConverter.msix'))
$hex = ($bytes[0..63] | ForEach-Object { $_.ToString('X2') }) -join ' '
Write-Host $hex
Write-Host ""

# ── Test 4: certificate EKU ───────────────────────────────────────────────────
Write-Host "=== Certificate EKU ==="
$cert.EnhancedKeyUsageList | ForEach-Object { Write-Host "  $($_.FriendlyName)  OID=$($_.ObjectId)" }
