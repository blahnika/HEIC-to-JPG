@echo off
echo ================================================
echo HEIC to JPG Converter - Setup
echo ================================================
echo.

echo Installing Python dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================
    echo Installation successful!
    echo ================================================
    echo.
    echo Next steps:
    echo 1. Double-click 'install_context_menu.reg' to add right-click menu
    echo 2. Right-click any HEIC file and select "Convert to JPG"
    echo.
    echo Or drag HEIC files onto heic_converter.py to convert them!
    echo ================================================
) else (
    echo.
    echo ================================================
    echo Error: Installation failed!
    echo ================================================
    echo.
    echo Please make sure Python is installed and added to PATH.
    echo Try running: python --version
    echo ================================================
)

echo.
pause
