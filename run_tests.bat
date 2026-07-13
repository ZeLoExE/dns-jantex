@echo off
setlocal

echo [1/3] Compiling Python files...
python -m compileall -q . || exit /b 1

echo [2/3] Running unit tests...
python -m pytest -q || exit /b 1

echo [3/3] Linting application modules...
python -m ruff check core ui main.py helper.py updater.py tests || exit /b 1

echo.
echo All automated checks passed.
endlocal
