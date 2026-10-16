@echo off
cd /d "%~dp0"
powershell -NoProfile -Command "Start-Process 'src-tauri\target\release\dns-jantex.exe' -Verb RunAs"
