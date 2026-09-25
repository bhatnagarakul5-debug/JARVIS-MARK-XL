@echo off
title J.A.R.V.I.S. Mark 58 (Creator: Akul Bhatnagar -- ESTD 2025)
cd /d "%~dp0"

:: 1. Check if virtual environment exists and has python
if exist "venv\Scripts\python.exe" (
    echo [JARVIS] Initializing JARVIS Mark 58 via virtual environment...
    venv\Scripts\python.exe main.py
    if %errorlevel% neq 0 pause
    exit /b %errorlevel%
)

:: 2. Check if system python is available
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [JARVIS] Initializing JARVIS Mark 58 via system Python...
    python main.py
    if %errorlevel% neq 0 pause
    exit /b %errorlevel%
)

:: 3. Check Python launcher (py -3)
py -3 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [JARVIS] Initializing JARVIS Mark 58 via Python Launcher (py -3)...
    py -3 main.py
    if %errorlevel% neq 0 pause
    exit /b %errorlevel%
)

:: 4. Check Python launcher (py)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [JARVIS] Initializing JARVIS Mark 58 via Python Launcher (py)...
    py main.py
    if %errorlevel% neq 0 pause
    exit /b %errorlevel%
)

:: 5. Check python3
python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [JARVIS] Initializing JARVIS Mark 58 via python3...
    python3 main.py
    if %errorlevel% neq 0 pause
    exit /b %errorlevel%
)

echo.
echo ================================================================
echo   [ERROR] No working Python environment found.
echo   Please ensure Python 3.10+ is installed and on your PATH.
echo   Or run setup.bat to set up the environment automatically!
echo ================================================================
echo.
pause
