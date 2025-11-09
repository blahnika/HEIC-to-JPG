@echo off
REM HEIC to JPG Converter - Context Menu Launcher
REM This batch file is called by the Windows context menu

python "%~dp0heic_converter.py" %*
