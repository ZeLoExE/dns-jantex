@echo off
REM Build script for DNS Changer application

echo Building DNS Changer...
echo.

REM Check if PyInstaller is installed
pyinstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Build the main application
echo Building DNSChanger.exe...
pyinstaller build.spec

REM Build the updater
echo Building Updater.exe...
pyinstaller build_updater.spec

echo.
echo Build complete!
echo   Main app:  dist\DNSChanger\
echo   Updater:   dist\Updater\Updater.exe
echo.
echo Copy Updater.exe to the dist\DNSChanger\ folder or project root.
echo.
pause
