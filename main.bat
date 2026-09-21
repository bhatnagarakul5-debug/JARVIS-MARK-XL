@echo off
title J.A.R.V.I.S. Mark 58 (Creator: Akul Bhatnagar -- ESTD 2025)
cd /d "%~dp0"

if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe main.py
    pause
    exit /b 0
)

python main.py >nul 2>&1
if %errorlevel% equ 0 (
    python main.py
    pause
    exit /b 0
)

py -3 main.py >nul 2>&1
if %errorlevel% equ 0 (
    py -3 main.py
    pause
    exit /b 0
)

py main.py >nul 2>&1
if %errorlevel% equ 0 (
    py main.py
    pause
    exit /b 0
)

echo [ERROR] No working Python environment found.
echo Please run setup.bat first!
pause
