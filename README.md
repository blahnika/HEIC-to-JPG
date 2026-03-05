# HEIC to JPG Converter

A Python-based tool to convert HEIC/HEIF images to JPG format with Windows context menu integration.

## Features

- Convert HEIC/HEIF files to high-quality JPG
- Batch convert multiple files at once
- Right-click context menu integration (Windows 10 and 11)
- Preserves image quality (95% quality default)
- Handles transparency properly (converts to white background)
- Fast and lightweight

## Installation

### 1. Install Python Dependencies

Make sure you have Python 3.7+ installed, then run:

```bash
pip install -r requirements.txt
```

This will install:

- Pillow (image processing)
- pillow-heif (HEIC format support)

### 2. Add Right-Click Context Menu

#### Windows 11

Windows 11's modern context menu requires a signed MSIX sparse package rather than a
simple registry entry. Run the installer script in PowerShell from the repo directory:

```powershell
.\install.ps1
```

The script will:
1. Build `launcher.exe` from source (requires [.NET 8 SDK](https://dotnet.microsoft.com/download/dotnet/8.0))
2. Create and trust a self-signed certificate (current user only, no admin needed)
3. Package and register the sparse MSIX so "Convert to JPG" appears directly in
   the first-level right-click menu for `.heic` and `.heif` files

**Prerequisites for `install.ps1`:**
- [.NET 8 SDK](https://dotnet.microsoft.com/download/dotnet/8.0)
- Windows SDK (`makeappx.exe` + `signtool.exe`) — install via
  [Visual Studio Installer](https://visualstudio.microsoft.com/) > Individual Components > "Windows SDK",
  or the [standalone Windows SDK](https://developer.microsoft.com/windows/downloads/windows-sdk/)

#### Windows 10

Double-click `install_context_menu.reg`, then click Yes and OK.
"Convert to JPG" will appear under "Show more options" when right-clicking a HEIC file.

## Usage

### Method 1: Right-Click Context Menu (After Installation)

1. Right-click on any `.heic` or `.heif` file
2. Select "Convert to JPG"
3. The converted file will appear in the same folder with a `.jpg` extension

### Method 2: Drag and Drop

1. Drag one or more HEIC files onto `heic_converter.py`
2. A command window will show conversion progress
3. Press Enter when complete

### Method 3: Command Line

Convert a single file:

```bash
python heic_converter.py photo.heic
```

Convert multiple files:

```bash
python heic_converter.py photo1.heic photo2.heic photo3.heic
```

Convert all HEIC files in a folder:

```bash
python heic_converter.py C:\Photos\MyFolder
```

## Uninstallation

#### Windows 11

```powershell
.\uninstall.ps1
```

#### Windows 10

Double-click `uninstall_context_menu.reg`, then click Yes and OK.

## How It Works

The converter:

1. Opens HEIC files using the `pillow-heif` library
2. Converts to RGB color mode (handling transparency)
3. Saves as high-quality JPG (95% quality, optimized)
4. Preserves the original filename, just changes the extension

On Windows 11, a thin `launcher.exe` shim receives the file path from the OS and
calls `heic_converter.py`. This is required because the MSIX sparse package manifest
needs a `.exe` as its entry point.

## Troubleshooting

**"Convert to JPG" appears under "Show more options" instead of the top-level menu (Windows 11):**

The `.reg` file method only works for the classic Windows 10 context menu. For the
Windows 11 first-level menu, use `install.ps1` — it registers a sparse MSIX package
which is the mechanism Windows 11 uses to surface custom context menu entries.

**`install.ps1` fails with "makeappx.exe not found":**

Install the Windows SDK. The quickest path is through Visual Studio Installer:
`Individual Components` > search "Windows SDK" > select the latest version.

**`install.ps1` fails with "dotnet not found":**

Install the [.NET 8 SDK](https://dotnet.microsoft.com/download/dotnet/8.0) and re-run.

**"Module not found" error when converting:**

- Make sure you ran `pip install -r requirements.txt`
- Try: `pip install Pillow pillow-heif`

**Python not found:**

- Make sure Python is installed and added to your PATH
- Try running: `python --version` in Command Prompt

**Context menu doesn't appear after install.ps1:**

- Try restarting Windows Explorer (Task Manager → Windows Explorer → Restart)
- Make sure you're running PowerShell from the repo root directory
- Check that the script completed without errors

## File Structure

```
HEIC-to-JPG/
├── heic_converter.py              # Main converter script
├── heic_converter_batch.py        # Multi-select batch wrapper
├── convert_heic.bat               # Batch launcher (drag-and-drop / Win10 menu)
├── launcher.exe                   # Thin shim for Win11 sparse package (pre-built)
├── sparse-package/
│   ├── AppxManifest.xml           # MSIX sparse package manifest
│   └── Assets/                    # App icons
├── src/
│   └── Launcher/                  # Source for launcher.exe
├── install.ps1                    # Windows 11 installer (sparse package)
├── uninstall.ps1                  # Windows 11 uninstaller
├── install_context_menu.reg       # Windows 10 registry installer
├── uninstall_context_menu.reg     # Windows 10 registry uninstaller
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Requirements

- Python 3.7 or higher
- Windows 10/11
- Pillow >= 10.0.0
- pillow-heif >= 0.13.0
- **Windows 11 context menu only:** .NET 8 SDK + Windows SDK

## License

Free to use and modify as needed!

## Notes

- Original HEIC files are not deleted or modified
- JPG files are saved with the same filename in the same location
- If a JPG file already exists, it will be overwritten
- Quality setting can be adjusted in `heic_converter.py` (line 15)
