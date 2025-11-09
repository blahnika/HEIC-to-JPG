# HEIC to JPG Converter

A simple Python-based tool to convert HEIC/HEIF images to JPG format with Windows context menu integration.

## Features

- 🖼️ Convert HEIC/HEIF files to high-quality JPG
- 📁 Batch convert multiple files at once
- 🖱️ Right-click context menu integration
- 🎨 Preserves image quality (95% quality default)
- 🔄 Handles transparency properly (converts to white background)
- ⚡ Fast and lightweight

## Installation

### 1. Install Python Dependencies

Make sure you have Python 3.7+ installed, then run:

```bash
pip install -r requirements.txt
```

This will install:
- Pillow (image processing)
- pillow-heif (HEIC format support)

### 2. Add Right-Click Context Menu (Optional)

To add "Convert to JPG" to your right-click menu for HEIC files:

1. Double-click `install_context_menu.reg`
2. Click "Yes" when Windows asks for permission
3. Click "OK" on the confirmation dialog

Now you can right-click any HEIC file and select "Convert to JPG"!

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

To remove the context menu integration:

1. Double-click `uninstall_context_menu.reg`
2. Click "Yes" when Windows asks for permission
3. Click "OK" on the confirmation dialog

## How It Works

The converter:
1. Opens HEIC files using the `pillow-heif` library
2. Converts to RGB color mode (handling transparency)
3. Saves as high-quality JPG (95% quality, optimized)
4. Preserves the original filename, just changes the extension

## Troubleshooting

**"Module not found" error:**
- Make sure you ran `pip install -r requirements.txt`
- Try: `pip install Pillow pillow-heif`

**Context menu doesn't appear:**
- Make sure you ran `install_context_menu.reg` as administrator
- Check that the path in the .reg file matches your installation location
- Try restarting Windows Explorer (Task Manager → Windows Explorer → Restart)

**Python not found:**
- Make sure Python is installed and added to your PATH
- Try running: `python --version` in Command Prompt

## File Structure

```
HEIC-to-JPG/
├── heic_converter.py          # Main converter script
├── convert_heic.bat           # Batch launcher for context menu
├── install_context_menu.reg   # Registry file to add context menu
├── uninstall_context_menu.reg # Registry file to remove context menu
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Requirements

- Python 3.7 or higher
- Windows 10/11
- Pillow >= 10.0.0
- pillow-heif >= 0.13.0

## License

Free to use and modify as needed!

## Notes

- Original HEIC files are not deleted or modified
- JPG files are saved with the same filename in the same location
- If a JPG file already exists, it will be overwritten
- Quality setting can be adjusted in the `heic_converter.py` file (line 15)
