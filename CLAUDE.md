# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Windows tool that converts HEIC/HEIF images to JPG. Supports drag-and-drop, command-line, and Windows context menu integration (Windows 10 via registry, Windows 11 via MSIX sparse package).

## Common Commands

### Python conversion (direct use)
```bash
python heic_converter.py photo.heic
python heic_converter.py photo1.heic photo2.heic
python heic_converter.py C:\Photos\MyFolder
pip install -r requirements.txt
```

### Windows 11 context menu installation
```powershell
.\install.ps1    # Build launcher.exe, create/trust cert, package+sign MSIX, register
.\uninstall.ps1  # Remove sparse package registration
```

### Build launcher.exe manually
```bash
dotnet publish src/Launcher/Launcher.csproj -r win-x64 -p:PublishSingleFile=true -p:SelfContained=false --output . --configuration Release
```

### Repack MSIX manually
```bash
python repack_msix.py HeicConverter.msix HeicConverter_fixed.msix
```

## Architecture

### Two-layer execution model (Windows 11)

The Windows 11 modern context menu requires a signed MSIX sparse package with a `.exe` entry point. Because the converter is Python, there's a shim:

1. **`sparse-package/AppxManifest.xml`** — declares file type associations for `.heic`/`.heif` and the verb `ConvertToJPG`, pointing to `launcher.exe`
2. **`src/Launcher/Program.cs`** → **`launcher.exe`** — a minimal .NET 8 C# shim that receives the file path from the OS and invokes `python heic_converter.py "<path>"`
3. **`heic_converter.py`** — the actual converter using Pillow + pillow-heif

### MSIX packaging quirks

`install.ps1` uses a `repack_msix.py` step after `makeappx.exe` because older versions of `makeappx` compress `AppxManifest.xml`, violating the MSIX spec (metadata must be ZIP_STORED). `repack_msix.py` rebuilds the MSIX with all entries uncompressed and regenerates `AppxBlockMap.xml` with correct SHA-256 hashes.

The install script also stages the MSIX through `%TEMP%` before repacking because Windows Store Python can't write to OneDrive-backed paths.

### Batch multi-select handling

When multiple HEIC files are right-clicked and converted simultaneously, the OS spawns one process per file. **`heic_converter_batch.py`** handles this via a temp-file queue (`%TEMP%/heic_converter_batch.json`) and a lock file (`%TEMP%/heic_converter_lock.tmp`): the first process acquires the lock, waits for the batch to stabilize (no new files for 0.5s), then converts all queued files together.

### Key files

| File | Purpose |
|------|---------|
| `heic_converter.py` | Core converter; quality default at line 14 (`quality=95`) |
| `heic_converter_batch.py` | Multi-select batch wrapper; imports from `heic_converter` |
| `src/Launcher/Program.cs` | .NET 8 shim (7 lines) — passes CLI args to Python |
| `sparse-package/AppxManifest.xml` | MSIX manifest; edit here to change verbs/file types |
| `install.ps1` | Full Win11 install pipeline (5 steps) |
| `repack_msix.py` | Fixes MSIX zip compression and regenerates BlockMap |

## Prerequisites

- Python 3.7+, Pillow ≥ 10.0.0, pillow-heif ≥ 0.13.0
- Windows 11 context menu only: .NET 8 SDK + Windows SDK (`makeappx.exe`, `signtool.exe`)
- The repo must live on a local (non-OneDrive-synced) path when running `install.ps1`, or `%TEMP%` staging handles it automatically
