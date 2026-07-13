@echo off
setlocal

echo Building DNS Jantex 3.0.4...

where pyinstaller >nul 2>&1
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed.
    echo Run: py -m pip install -r requirements-dev.txt
    exit /b 1
)

pyinstaller --clean --noconfirm build.spec || exit /b 1
pyinstaller --clean --noconfirm build_updater.spec || exit /b 1
pyinstaller --clean --noconfirm build_helper.spec || exit /b 1

echo.
echo Build complete:
echo   Main app:  dist\DNSChanger\
echo   Updater:   dist\Updater.exe
echo   Helper:    dist\DNSHelper.exe
echo.
echo IMPORTANT: Sign all EXEs and the final installer before publishing.
endlocal
