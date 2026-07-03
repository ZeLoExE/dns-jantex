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

REM Build the application
echo Building standalone executable...
pyinstaller build.spec

echo.
echo Build complete! Output in dist\DNSChanger\
echo.
pause
